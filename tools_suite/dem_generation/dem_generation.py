# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QDialog
from qgis.core import QgsProject, QgsRasterLayer, QgsProcessingException, QgsTask, QgsApplication, QgsMessageLog, Qgis
import processing

# --- Method-specific imports ---
from osgeo import gdal, osr
from scipy.interpolate import griddata

# --- Dialog imports ---
from .dem_generation_dialog import DemGenerationDialog

# ---------------------------------
# --- Bare Earth DEM Generation ---
# --------------------------------------------------------------------------------------------
# Description:
# This function generates a bare earth DEM from LiDAR point clouds by filtering ground points,
# creating a raster grid and filling gaps using nearest-neighbor interpolation.
# It allows users to specify the cell size for the DEM.
# --------------------------------------------------------------------------------------------

# -------------------------------------------
# --- Background Task for DEM Generation ---
# -------------------------------------------

class DemGenerationTask(QgsTask):
    """Generate DEM from a LiDAR file in a background thread"""

    def __init__(self, description, filename, output_path, cell_size, use_triangulation, parent, hillshade_requested, translator, hillshade_output_path=None):
        super().__init__(description, QgsTask.CanCancel)
        self.filename = filename
        self.output_path = output_path
        self.cell_size = cell_size
        self.use_triangulation = use_triangulation
        self.parent = parent
        self.hillshade_requested = hillshade_requested
        self.hillshade_output_path = hillshade_output_path

        self.exception = None
        self.tr = translator
        self.hillshade_path = None

    def run(self):
        try:
            # Step 1: Read input file
            las = laspy.read(self.filename, laz_backend=LazBackend.Lazrs)
            self.setProgress(10)

            # Step 2: Filter ground points
            ground_mask = (las.classification == 2)
            if not np.any(ground_mask):
                raise ValueError(self.tr("No ground points found in the file"))
            x = las.x[ground_mask]
            y = las.y[ground_mask]
            z = las.z[ground_mask]
            min_x, max_x = x.min(), x.max()
            min_y, max_y = y.min(), y.max()
            cols = int(np.ceil((max_x - min_x) / self.cell_size))
            rows = int(np.ceil((max_y - min_y) / self.cell_size))
            self.setProgress(20)

            # Step 2.1: CRS extraction
            srs = osr.SpatialReference()
            try:
                from laspy.vlrs.known import WktCoordinateSystemVlr
                wkt_vlrs = [vlr for vlr in las.header.vlrs if isinstance(vlr, WktCoordinateSystemVlr)]
                if wkt_vlrs:
                    srs.ImportFromWkt(wkt_vlrs[0].wkt)
                else:
                    srs.ImportFromEPSG(4326)
            except Exception:
                srs.ImportFromEPSG(4326)
            self.setProgress(30)

            # Step 3: DEM Generation
            if self.use_triangulation:
                # Step 3.1: Triangulation-based interpolation (TIN)
                grid_x, grid_y = np.meshgrid(
                    np.linspace(min_x, max_x, cols),
                    np.linspace(max_y, min_y, rows)
                )
                self.setProgress(40)

                dem = griddata(
                    (x, y), z,
                    (grid_x, grid_y),
                    method='linear'
                )
                self.setProgress(60)

                # Fill gaps with nearest-neighbor
                dem = np.where(
                    np.isnan(dem),
                    griddata((x, y), z, (grid_x, grid_y), method='nearest'),
                    dem
                )
                self.setProgress(80)

            else:
                # Step 3.2: Cell-based minimum Z value (bare earth assumption)

                dem = np.full((rows, cols), np.nan, dtype=np.float32)

                col_idx = ((x - min_x) / self.cell_size).astype(int)
                row_idx = ((max_y - y) / self.cell_size).astype(int)

                total_points = len(z)
                for i, (r, c, z_val) in enumerate(zip(row_idx, col_idx, z), start=1):
                    if self.isCanceled():
                        return False

                    if 0 <= r < rows and 0 <= c < cols:
                        if np.isnan(dem[r, c]) or z_val < dem[r, c]:
                            dem[r, c] = z_val

                    if i % 10000 == 0 or i == total_points:
                        progress = 30 + (50 * i / total_points)
                        self.setProgress(progress)

            # Step 4: Replace NaNs with -9999 (to mark nodata for GDAL)
            dem = np.where(np.isnan(dem), -9999, dem)

            driver = gdal.GetDriverByName('GTiff')
            out_raster = driver.Create(self.output_path, cols, rows, 1, gdal.GDT_Float32)
            out_raster.SetGeoTransform((min_x, self.cell_size, 0, max_y, 0, -self.cell_size))

            out_raster.SetProjection(srs.ExportToWkt())
            out_band = out_raster.GetRasterBand(1)
            out_band.WriteArray(dem)
            out_band.SetNoDataValue(-9999)
            out_band.FlushCache()
            self.setProgress(90)

            # Hybrid step: Fill Nodata gaps with GDAL's FillNodata
            gdal.FillNodata(targetBand=out_band, maskBand=None,
                            maxSearchDist=10, smoothingIterations=1)

            dem_min, dem_max = float(np.nanmin(dem[dem != -9999])), float(np.nanmax(dem[dem != -9999]))
            out_band.ComputeStatistics(False)
            out_band.SetStatistics(dem_min, dem_max, 0, 0)
            out_raster = None

            # Step 5: Generate hillshade (optional)
            if self.hillshade_requested:
                suffix = "_hillshade_TIN" if self.use_triangulation else "_hillshade"

                self.hillshade_path = (
                    self.hillshade_output_path
                    if self.hillshade_output_path
                    else os.path.splitext(self.output_path)[0] + suffix + ".tif"
                )

                try:
                    processing_params = {
                        'INPUT': self.output_path,
                        'Z_FACTOR': 1.0,
                        'AZIMUTH': 315.0,
                        'V_ANGLE': 45.0,
                        'OUTPUT': self.hillshade_path
                    }
                    processing.run("native:hillshade", processing_params)
                except QgsProcessingException:
                    self.hillshade_path = None
            self.setProgress(100)
            return True

        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        try:
            if result:
                dem_layer_name = os.path.splitext(os.path.basename(self.output_path))[0]
                dem_layer = QgsRasterLayer(self.output_path, dem_layer_name)
                if dem_layer.isValid():
                    QgsProject.instance().addMapLayer(dem_layer)

                if self.hillshade_path:
                    hillshade_layer_name = os.path.splitext(os.path.basename(self.hillshade_path))[0]
                    hillshade_layer = QgsRasterLayer(self.hillshade_path, hillshade_layer_name)
                    if hillshade_layer.isValid():
                        QgsProject.instance().addMapLayer(hillshade_layer)

                msg = f"{self.tr('DEM successfully generated from ground points. Output saved at')}:{self.output_path}"
                if self.hillshade_path:
                    msg += f"\n\n{self.tr('Hillshade saved at')}:\n{self.hillshade_path}"

                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Bare Earth DEM Generated"),
                    msg
                )
            else:
                msg = f"{self.tr('An error occurred')}: {self.exception}" if self.exception else self.tr("DEM generation failed")
                QgsMessageLog.logMessage(msg, "MyLiDAR", Qgis.Critical)
                QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error whilst generating Bare Earth DEM"), msg)
        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# ---------------------------------
# --- Bare Earth DEM Generation ---
# ---------------------------------

def generate_bare_earth_dem(self):
    dialog = DemGenerationDialog(self.iface.mainWindow(), translator=self.tr)
    if dialog.exec_() != QDialog.Accepted:
        return

    input_path, output_path = dialog.get_input_output()
    cell_size, use_triangulation, hillshade_requested = dialog.get_values()

    if not input_path:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Input Selected"),
            self.tr("Please select a LiDAR layer or file.")
        )
        return

    if not output_path:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Output Selected"),
            self.tr("Please specify an output DEM file path.")
        )
        return

    hillshade_output_path = None
    if hillshade_requested:
        default_hillshade = os.path.splitext(output_path)[0] + "_hillshade.tif"
        hillshade_output_path, _ = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            self.tr("Save Hillshade Raster"),
            default_hillshade,
            "GeoTIFF (*.tif)"
        )
        if not hillshade_output_path:
            hillshade_requested = False

    # Step 2: Create and run the background task
    task_desc = f"{self.tr('Generating DEM from')} {os.path.basename(input_path)}"
    task = DemGenerationTask(task_desc, input_path, output_path, cell_size, use_triangulation, self, hillshade_requested, self.tr, hillshade_output_path)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Generating DEM in the background"),
        level=Qgis.Info,
        duration=-1
    )
