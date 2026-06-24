# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from qgis.core import QgsProject, QgsRasterLayer, QgsProcessingException, QgsTask, QgsApplication, QgsMessageLog, Qgis, QgsCoordinateReferenceSystem, QgsPointCloudLayer
import processing
from qgis.PyQt.QtCore import QDateTime

# --- Method-specific imports ---
from osgeo import gdal, osr
from scipy.interpolate import griddata
from laspy.vlrs.known import WktCoordinateSystemVlr

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

    def __init__(self, description, input_filename, output_path, cell_size, use_triangulation, parent, hillshade_requested, z_factor, azimuth, vertical_angle, translator, hillshade_output_path=None, log_filename=None):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.output_path = output_path
        self.cell_size = cell_size
        self.use_triangulation = use_triangulation
        self.parent = parent
        self.hillshade_requested = hillshade_requested
        self.hillshade_output_path = hillshade_output_path
        self.z_factor = z_factor
        self.azimuth = azimuth
        self.vertical_angle = vertical_angle
        self.hillshade_path = None
        self.output_crs = None
        self.exception = None
        self.tr = translator
        self.log_filename = log_filename
        self.log_entries = []

    def log_step(self, step_name, details="", relevancy="info"):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        levels = {
            "info": (Qgis.Info, self.tr("INFO")),
            "warning": (Qgis.Warning, self.tr("WARNING")),
            "critical": (Qgis.Critical, self.tr("CRITICAL"))
        }
        level = levels.get(relevancy, levels["info"])
        entry = f"[{timestamp}] {level[1]}  {step_name}: {details}"
        self.log_entries.append(entry)
        QgsMessageLog.logMessage(f"{step_name}: {details}", "MyLiDAR", level[0])

    def run(self):
        try:
            self.log_step(self.tr("PROCESS START"), f"Input: {os.path.basename(self.input_filename)}, Cell Size: {self.cell_size}, Triangulation: {self.use_triangulation}, Hillshade: {self.hillshade_requested}")

            # Step 1: Read input file
            self.log_step(self.tr("READING INPUT FILE"), self.input_filename, "info")
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            pycrs = las.header.parse_crs(prefer_wkt=True)
            if pycrs:
                self.output_crs = QgsCoordinateReferenceSystem(pycrs.to_wkt())
                self.log_step(self.tr("CRS DETECTED"), f"From file header: {self.output_crs.authid()}", "info")
            else:
                self.log_step(self.tr("CRS NOT FOUND"), self.tr("No CRS found in file header. Checking input layer loaded in QGIS"), "warning")

                matched_layer = None
                for lyr in QgsProject.instance().mapLayers().values():
                    if isinstance(lyr, QgsPointCloudLayer) and lyr.source() == self.input_filename:
                        matched_layer = lyr
                        break

                if matched_layer:
                    if matched_layer.crs().isValid():
                        self.output_crs = matched_layer.crs()
                        self.log_step(self.tr("CRS ASSIGNED"), f"{self.tr('Using CRS assigned in QGIS')}: {self.output_crs.authid()}", "info")

                    else:
                        self.log_step(self.tr("INVALID CRS"), self.tr("Matched layer CRS is invalid, no CRS will be assigned"), "warning")

                else:
                    self.log_step(self.tr("NO LAYER MATCH"), self.tr("Input file not found among loaded layers. Cannot import CRS from QGIS"), "warning")

            self.setProgress(10)

            # Step 2: Filter ground points
            self.log_step(self.tr("FILTERING GROUND POINTS"), "Using classification code 2 (ground)", "info")
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
            self.log_step(self.tr("GROUND POINTS FILTERED"), f"Points: {len(z)}, Extent: ({min_x}, {min_y}, {max_x}, {max_y}), Grid Size: ({cols} cols x {rows} rows)", "info")
            self.setProgress(20)

            # Step 2.1: CRS extraction
            srs = osr.SpatialReference()
            try:
                self.log_step(self.tr("EXTRACTING CRS"), "Attempting to read CRS from LAS file VLRs", "info")
                wkt_vlrs = [vlr for vlr in las.header.vlrs if isinstance(vlr, WktCoordinateSystemVlr)]
                if wkt_vlrs:
                    srs.ImportFromWkt(wkt_vlrs[0].wkt)
                    self.log_step(self.tr("CRS IMPORTED"), f"Successfully imported CRS from VLR: {srs.GetAttrValue('AUTHORITY', 1)}", "info")
                else:
                    srs.ImportFromEPSG(4326)
                    self.log_step(self.tr("CRS DEFAULTED"), "No WKT VLR found, defaulting to EPSG:4326", "warning")
            except Exception:
                srs.ImportFromEPSG(4326)
                self.log_step(self.tr("CRS ERROR"), "Error reading CRS from VLRs, defaulting to EPSG:4326", "warning")
            self.setProgress(30)

            # Step 3: DEM Generation
            if self.use_triangulation:
                self.log_step(self.tr("DEM GENERATION"), "Using triangulation-based interpolation (TIN)", "info")
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
                self.log_step(self.tr("DEM GENERATION"), "Using cell-based minimum Z value (bare earth assumption)", "info")
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
                self.log_step(self.tr("HILLSHADE GENERATION"), "Generating hillshade from DEM", "info")
                suffix = "_TIN" if self.use_triangulation else "_cell"
                self.hillshade_path = (
                    self.hillshade_output_path
                    if self.hillshade_output_path
                    else os.path.splitext(self.output_path)[0] + suffix + ".tif"
                )
                try:
                    processing_params = {
                        'INPUT': self.output_path,
                        'Z_FACTOR': self.z_factor,
                        'AZIMUTH': self.azimuth,
                        'V_ANGLE': self.vertical_angle,
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
                    if self.output_crs and self.output_crs.isValid():
                        dem_layer.setCrs(self.output_crs)
                        self.log_step(self.tr("CRS ASSIGNED TO DEM"), f"{self.tr('DEM CRS set to')}: {self.output_crs.authid()}", "info")
                    QgsProject.instance().addMapLayer(dem_layer)

                if self.hillshade_path:
                    hillshade_layer_name = os.path.splitext(os.path.basename(self.hillshade_path))[0]
                    hillshade_layer = QgsRasterLayer(self.hillshade_path, hillshade_layer_name)

                    if hillshade_layer.isValid():
                        if self.output_crs and self.output_crs.isValid():
                            hillshade_layer.setCrs(self.output_crs)
                            self.log_step(self.tr("CRS ASSIGNED TO HILLSHADE"), f"{self.tr('Hillshade CRS set to')}: {self.output_crs.authid()}", "info")
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
                if self.exception:
                    self.log_step(self.tr("ERROR EXCEPTION"), f"{self.tr('An error occurred during Bare Earth DEM Generation')}: {self.exception}", "critical")
                    QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error generating DEM"), f"{self.tr('An error occurred')}:\n{self.exception}")
                else:
                    self.log_step(self.tr("TASK CANCELED"), self.tr('Bare Earth DEM Generation was canceled by the user'), "info")

            if self.log_filename:
                try:
                    with open(self.log_filename, 'w', encoding='utf-8') as f:
                        f.write(f"MyLiDAR BARE EARTH DEM GENERATION REPORT\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(f"Input file: {self.input_filename}\n")
                        f.write(f"Output DEM: {self.output_path}\n")
                        f.write(f"Cell size: {self.cell_size}\n")
                        f.write(f"Triangulation used: {'Yes' if self.use_triangulation else 'No'}\n")
                        f.write(f"CRS: {self.output_crs.authid() if self.output_crs else 'Not set'}\n")
                        if self.hillshade_requested:
                            f.write(f"Hillshade: {self.hillshade_path}\n")
                            f.write(f"Hillshade parameters: Z Factor={self.z_factor}, Azimuth={self.azimuth}, Vertical Angle={self.vertical_angle}\n")
                        f.write("PROCESSING STEPS:\n")
                        f.write("-" * 30 + "\n")
                        for entry in self.log_entries:
                            f.write(entry + "\n")

                        if not result and self.exception:
                            f.write(f"\nFINAL STATUS: FAILED\nError: {str(self.exception)}\n")
                        else:
                            f.write(f"\nFINAL STATUS: SUCCESS\n")

                    self.log_step(self.tr("LOG FILE WRITTEN"), self.log_filename, "info")

                except Exception as log_error:
                    QgsMessageLog.logMessage(
                        f"Failed to write log file {self.log_filename}: {log_error}",
                        "MyLiDAR", Qgis.Warning
                    )

        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# ---------------------------------
# --- Bare Earth DEM Generation ---
# ---------------------------------

def generate_bare_earth_dem(self):
    dialog = DemGenerationDialog(self.iface.mainWindow(), translator=self.tr)
    if dialog.exec() != QDialog.accepted:
        return

    input_path, output_path = dialog.get_input_output()
    cell_size, use_triangulation, hillshade_requested, hillshade_path, z_factor, azimuth, vertical_angle = dialog.get_values()
    log_filename = dialog.get_log_path()

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

    # Step 2: Create and run the background task
    task_desc = f"{self.tr('Generating DEM from')} {os.path.basename(input_path)}"
    task = DemGenerationTask(task_desc, input_path, output_path, cell_size, use_triangulation, self, hillshade_requested, z_factor, azimuth, vertical_angle, self.tr, hillshade_path, log_filename)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Generating DEM in the background"),
        level=Qgis.Info,
        duration=-1
    )
