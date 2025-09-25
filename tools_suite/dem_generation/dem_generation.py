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
# ---------------------------------
# Description:
# This function generates a bare earth DEM from LiDAR point clouds by filtering ground points,
# creating a raster grid and filling gaps using nearest-neighbor interpolation.
# It allows users to specify the cell size for the DEM.
# ---------------------------------

# -------------------------------------------
# --- Background Task for DEM Generation ---
# -------------------------------------------

class DemGenerationTask(QgsTask):
    """Generate DEM from a LiDAR file in a background thread"""

    def __init__(self, description, filename, output_path, cell_size, use_triangulation, parent, hillshade_requested):
        super().__init__(description, QgsTask.CanCancel)
        self.filename = filename
        self.output_path = output_path
        self.cell_size = cell_size
        self.use_triangulation = use_triangulation
        self.parent = parent
        self.hillshade_requested = hillshade_requested

        self.exception = None
        self.hillshade_path = None

    def run(self):
        try:
            las = laspy.read(self.filename, laz_backend=LazBackend.Lazrs)

            ground_mask = (las.classification == 2)  # Filter ground points
            if not np.any(ground_mask):
                raise ValueError("No ground points found in the file.")

            x = las.x[ground_mask]
            y = las.y[ground_mask]
            z = las.z[ground_mask]
            min_x, max_x = x.min(), x.max()
            min_y, max_y = y.min(), y.max()
            cols = int(np.ceil((max_x - min_x) / self.cell_size))
            rows = int(np.ceil((max_y - min_y) / self.cell_size))

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

            # --- DEM Generation ---
            if self.use_triangulation:
                # Triangulation-based interpolation (TIN)
                grid_x, grid_y = np.meshgrid(
                    np.linspace(min_x, max_x, cols),
                    np.linspace(max_y, min_y, rows)
                )

                dem = griddata(
                    (x, y), z,
                    (grid_x, grid_y),
                    method='linear'
                )

                # Fill gaps with nearest-neighbor
                dem = np.where(
                    np.isnan(dem),
                    griddata((x, y), z, (grid_x, grid_y), method='nearest'),
                    dem
                )

            else:
                # Cell-based minimum Z value (bare earth assumption)
                dem = np.full((rows, cols), np.nan, dtype=np.float32)

                col_idx = ((x - min_x) / self.cell_size).astype(int)
                row_idx = ((max_y - y) / self.cell_size).astype(int)

                for r, c, z_val in zip(row_idx, col_idx, z):
                    if 0 <= r < rows and 0 <= c < cols:
                        if np.isnan(dem[r, c]) or z_val < dem[r, c]:
                            dem[r, c] = z_val

            # Replace NaNs with -9999 (to mark nodata for GDAL)
            dem = np.where(np.isnan(dem), -9999, dem)

            driver = gdal.GetDriverByName('GTiff')
            out_raster = driver.Create(self.output_path, cols, rows, 1, gdal.GDT_Float32)
            out_raster.SetGeoTransform((min_x, self.cell_size, 0, max_y, 0, -self.cell_size))

            out_raster.SetProjection(srs.ExportToWkt())
            out_band = out_raster.GetRasterBand(1)
            out_band.WriteArray(dem)
            out_band.SetNoDataValue(-9999)
            out_band.FlushCache()

            # Hybrid step: Fill Nodata gaps with GDAL's FillNodata
            gdal.FillNodata(targetBand=out_band, maskBand=None,
                            maxSearchDist=10, smoothingIterations=1)

            dem_min, dem_max = float(np.nanmin(dem[dem != -9999])), float(np.nanmax(dem[dem != -9999]))
            out_band.ComputeStatistics(False)
            out_band.SetStatistics(dem_min, dem_max, 0, 0)
            out_raster = None

            # Optionally generate hillshade
            if self.hillshade_requested:
                suffix = "_hillshade_TIN" if self.use_triangulation else "_hillshade"
                self.hillshade_path = os.path.splitext(self.output_path)[0] + suffix + '.tif'
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

                msg = f"DEM successfully generated from ground points.\nOutput saved at:\n{self.output_path}"
                if self.hillshade_path:
                    msg += f"\n\nHillshade saved at:\n{self.hillshade_path}"

                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    "Bare Earth DEM Generated",
                    msg
                )
            else:
                msg = f"An error occurred: {self.exception}" if self.exception else "DEM generation failed."
                QgsMessageLog.logMessage(msg, "MyPlugin", Qgis.Critical)
                QMessageBox.critical(self.parent.iface.mainWindow(), "Error whilst generating Bare Earth DEM", msg)
        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# ---------------------------------
# --- Bare Earth DEM Generation ---
# ---------------------------------

def generate_bare_earth_dem(self):
    # Step 1: Select input file path
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File for Bare Earth DEM',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not filename:
        return

    # Step 2: Get parameters via a custom dialog
    dlg = DemGenerationDialog(self.iface.mainWindow())
    if dlg.exec_() != QDialog.Accepted:
        return
    cell_size, use_triangulation = dlg.get_values()

    # Step 3: Select input file path
    suffix = "_bare_earth_dem_TIN" if use_triangulation else "_bare_earth_dem"
    default_name = os.path.splitext(filename)[0] + suffix + ".tif"
    output_path, _ = QFileDialog.getSaveFileName(
        self.iface.mainWindow(),
        'Save Bare Earth DEM',
        default_name,
        'GeoTIFF (*.tif)'
    )
    if not output_path:
        return

    # Stesp 4: Select hillshade generation
    reply = QMessageBox.question(
        self.iface.mainWindow(),
        "Generate Hillshade?",
        "Do you also want to create a hillshade raster from the DEM?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    hillshade_requested = (reply == QMessageBox.Yes)

    # Step 5: Create and run the background task
    task_desc = f"Generating DEM from {os.path.basename(filename)}"
    task = DemGenerationTask(task_desc, filename, output_path, cell_size, use_triangulation, self, hillshade_requested)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        "Task Started",
        "DEM generation running in the background...",
        level=Qgis.Info,
        duration=-1
    )
