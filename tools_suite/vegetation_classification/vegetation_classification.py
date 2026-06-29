# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsPointCloudLayer, QgsProject, QgsTask, QgsApplication, Qgis, QgsMessageLog, QgsCoordinateReferenceSystem

# --- Method-specific imports ---
from scipy.spatial import cKDTree

# --- Dialog imports ---
from .vegetation_classification_dialog import VegetationClassificationDialog

# --- Utils imports ---
from ..utils import log_step

# ---------------------------------
# --- Vegetation Classification ---
# --------------------------------------------------------------------------------------
# Description:
# This module classifies vegetation in LiDAR data into low, medium, and high categories,
# based on user-defined height thresholds.
# --------------------------------------------------------------------------------------

# -----------------------------------------------------
# --- Background Task for Vegetation Classification ---
# -----------------------------------------------------

class VegetationClassificationTask(QgsTask):
    """Background task for classifying LiDAR vegetation points"""

    def __init__(self, description, input_filename, output_filename, low_thresh, high_thresh, grass_enabled, parent, translator, log_filename=None):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.low_thresh = low_thresh
        self.high_thresh = high_thresh
        self.grass_enabled = grass_enabled
        self.parent = parent
        self.exception = None
        self.tr = translator
        self.stats = None
        self.output_crs = None
        self.log_filename = log_filename
        self.log_entries = []

    def run(self):
        try:
            log_step(self, self.tr("PROCESS START"), f"Input: {os.path.basename(self.input_filename)}, Low Thresh: {self.low_thresh}, High Thresh: {self.high_thresh}, Grass Enabled: {self.grass_enabled}"),

            # Step 1: Read input file
            log_step(self, self.tr("READING INPUT FILE"), self.input_filename, "info")
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            pycrs = las.header.parse_crs(prefer_wkt=True)
            if pycrs:
                self.output_crs = QgsCoordinateReferenceSystem(pycrs.to_wkt())
                log_step(self, self.tr("CRS DETECTED"), f"From file header: {self.output_crs.authid()}", "info")
            else:
                log_step(self, self.tr("CRS NOT FOUND"), self.tr("No CRS found in file header. Checking input layer loaded in QGIS"), "warning")

                matched_layer = None
                for lyr in QgsProject.instance().mapLayers().values():
                    if isinstance(lyr, QgsPointCloudLayer) and lyr.source() == self.input_filename:
                        matched_layer = lyr
                        break

                if matched_layer:
                    if matched_layer.crs().isValid():
                        self.output_crs = matched_layer.crs()
                        log_step(self, self.tr("CRS ASSIGNED"), f"{self.tr('Using CRS assigned in QGIS')}: {self.output_crs.authid()}", "info")

                    else:
                        log_step(self, self.tr("INVALID CRS"), self.tr("Matched layer CRS is invalid, no CRS will be assigned"), "warning")

                else:
                    log_step(self, self.tr("NO LAYER MATCH"), self.tr("Input file not found among loaded layers. Cannot import CRS from QGIS"), "warning")

            # Step 2: Data preparation
            log_step(self, self.tr("DATA PREPARATION"), self.tr("Filtering ground and high vegetation points, and optionally classifying grass based on color"), "info")
            ground_class = 2
            low_class = 3
            medium_class = 4
            high_class = 5
            classifications = las.classification
            self.setProgress(20)

            # Optional grass classification from ground color
            num_grass = 0
            if self.grass_enabled:
                log_step(self, self.tr("GRASS CLASSIFICATION"), self.tr("Classifying grass points based on RGB values of ground points"), "info")
                dims = list(las.point_format.dimension_names)
                if all(d in dims for d in ("red", "green", "blue")):
                    r16 = las.red.astype(np.float32)
                    g16 = las.green.astype(np.float32)
                    b16 = las.blue.astype(np.float32)

                    r = (r16 / 256.0).astype(np.float32)
                    g = (g16 / 256.0).astype(np.float32)
                    b = (b16 / 256.0).astype(np.float32)

                    ground_idx = np.where(classifications == ground_class)[0]
                    if len(ground_idx) > 0:
                        rr = r[ground_idx]
                        gg = g[ground_idx]
                        bb = b[ground_idx]

                        total = rr + gg + bb + 1e-6
                        green_ratio = gg / total
                        exg = 2.0 * gg - rr - bb

                        grass_mask = (
                            (green_ratio > 0.33) &
                            (exg > 5.0) &
                            (gg > 20.0)
                        )

                        grass_idx = ground_idx[grass_mask]
                        classifications[grass_idx] = low_class
                        num_grass = int(grass_mask.sum())

            # Step 3: Filter ground points
            ground_idx = np.where(classifications == ground_class)[0]
            if len(ground_idx) == 0:
                gp_error_msg = self.tr("No ground points (class 2) found in the file. Cannot classify vegetation without ground reference.")
                log_step(self, self.tr("GROUND POINTS MISSING"), gp_error_msg, "critical")
                raise ValueError(gp_error_msg)

            ground_xy = np.vstack((las.x[ground_idx], las.y[ground_idx])).T
            ground_z = las.z[ground_idx]
            log_step(self, self.tr("GROUND POINTS FILTERED"), f"{len(ground_idx)} ground points found", "info")
            self.setProgress(30)

            # Step 4: Filter points originally marked as high vegetation
            high_veg_idx = np.where(classifications == high_class)[0]
            if len(high_veg_idx) == 0:
                no_hv_error_msg = self.tr("No high vegetation points (class 5) found in the file. Cannot reclassify vegetation.")
                log_step(self, self.tr("HIGH VEGETATION MISSING"), no_hv_error_msg, "critical")
                raise ValueError(no_hv_error_msg)

            veg_xy = np.vstack((las.x[high_veg_idx], las.y[high_veg_idx])).T
            veg_z = las.z[high_veg_idx]
            log_step(self, self.tr("HIGH VEGETATION FILTERED"), f"{len(high_veg_idx)} high vegetation points found for reclassification", "info")
            self.setProgress(40)

            # Step 5: Interpolate local ground height using nearest neighbor
            tree = cKDTree(ground_xy)
            n_points = veg_xy.shape[0]
            batch_size = max(10000, n_points // 100)  # ~100 progress updates
            local_ground_z = np.empty(n_points, dtype=np.float32)

            for i in range(0, n_points, batch_size):
                if self.isCanceled():
                    return False

                j = min(i + batch_size, n_points)
                _, nearest_ground_idx = tree.query(veg_xy[i:j], k=1)
                local_ground_z[i:j] = ground_z[nearest_ground_idx]

                # Update progress proportionally (40-80%)
                progress = 40 + (40 * j / n_points)
                self.setProgress(progress)

            veg_height = veg_z - local_ground_z
            log_step(self, self.tr("GROUND HEIGHT INTERPOLATED"), self.tr("Local ground height interpolated for vegetation points"), "info")

            # Step 6: Reclassify vegetation
            low_mask = veg_height < self.low_thresh
            medium_mask = (veg_height >= self.low_thresh) & (veg_height <= self.high_thresh)
            high_mask = veg_height > self.high_thresh

            las.classification[high_veg_idx[low_mask]] = low_class
            las.classification[high_veg_idx[medium_mask]] = medium_class
            las.classification[high_veg_idx[high_mask]] = high_class
            log_step(self, self.tr("VEGETATION RECLASSIFIED"), f"Low: {low_mask.sum()}, Medium: {medium_mask.sum()}, High: {high_mask.sum()}", "info")
            self.setProgress(90)

            # Step 7: Save results
            log_step(self, self.tr("WRITING OUTPUT FILE"), self.output_filename, "info")
            las.write(self.output_filename)
            log_step(self, self.tr("OUTPUT FILE WRITTEN"), f"File saved to {self.output_filename}", "info")

            self.stats = {
                "num_high_orig": len(high_veg_idx),
                "num_low": int(np.sum(low_mask)),
                "num_medium": int(np.sum(medium_mask)),
                "num_high": int(np.sum(high_mask)),
                "num_grass": num_grass,
                "grass_enabled": self.grass_enabled,
            }
            self.setProgress(100)
            log_step(self, self.tr("PROCESS COMPLETE"), f"Vegetation classification completed successfully with {self.stats['num_low']} low, {self.stats['num_medium']} medium, and {self.stats['num_high']} high vegetation points", "info")
            return True

        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        try:
            if result:
                layer_name = os.path.splitext(os.path.basename(self.output_filename))[0]
                pc_layer = QgsPointCloudLayer(self.output_filename, layer_name, "pdal")
                if pc_layer.isValid():
                    if self.output_crs and self.output_crs.isValid():
                        pc_layer.setCrs(self.output_crs)
                        log_step(self, self.tr("LAYER CRS APPLIED"), f"{self.tr('Output layer CRS applied')}: {self.output_crs.authid()}", "info")
                    else:
                        log_step(self, self.tr("NO CRS FOR LAYER"), self.tr("No valid CRS available to assign to the output layer"), "warning")
                    QgsProject.instance().addMapLayer(pc_layer)
                    log_step(self, self.tr("LAYER ADDED TO PROJECT"), layer_name, "info")
                else:
                    log_step(self, self.tr("LAYER LOAD FAILED"), self.tr("The LiDAR file was saved but could not be loaded into QGIS"), "warning")

                s = self.stats
                grass_line = ""
                if s.get("grass_enabled"):
                    grass_line = f"{self.tr('Grass (color-based from ground)')}: {s['num_grass']:,}\n"

                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Vegetation Reclassification Complete"),
                    f"{self.tr('Original high veg points')}: {s['num_high_orig']:,}\n"
                    f"{self.tr('Low vegetation')} (<{self.low_thresh} m): {s['num_low']:,}\n"
                    f"{self.tr('Medium vegetation')} ({self.low_thresh}-{self.high_thresh} m): {s['num_medium']:,}\n"
                    f"{self.tr('High vegetation')} (>{self.high_thresh} m): {s['num_high']:,}\n\n"
                    f"{grass_line}\n"
                    f"{self.tr('Updated file saved to')}:\n{self.output_filename}"
                )
            else:
                if self.exception:
                    log_step(self, self.tr("ERROR EXCEPTION"), f"{self.tr('An error occurred during vegetation classification')}: {self.exception}", "critical")
                    QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error During Classification"), f"{self.tr('An error occurred')}:\n{self.exception}")
                else:
                    log_step(self, self.tr("TASK CANCELED"), self.tr('Vegetation classification was canceled by the user'), "info")

            if self.log_filename:
                try:
                    with open(self.log_filename, 'w', encoding='utf-8') as f:
                        f.write(f"MyLiDAR VEGETATION CLASSIFICATION REPORT\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(f"Input file: {self.input_filename}\n")
                        f.write(f"Output file: {self.output_filename}\n")
                        f.write(f"Low threshold: {self.low_thresh}\n")
                        f.write(f"High threshold: {self.high_thresh}\n")
                        f.write(f"Grass classification enabled: {self.grass_enabled}\n")
                        f.write(f"CRS: {self.output_crs.authid() if self.output_crs else 'Not set'}\n")
                        f.write(f"Points reclassified as low vegetation: {self.stats['num_low'] if self.stats else 'N/A'}\n")
                        f.write(f"Points reclassified as medium vegetation: {self.stats['num_medium'] if self.stats else 'N/A'}\n")
                        f.write(f"Points reclassified as high vegetation: {self.stats['num_high'] if self.stats else 'N/A'}\n")
                        f.write("PROCESSING STEPS:\n")
                        f.write("-" * 30 + "\n")
                        for entry in self.log_entries:
                            f.write(entry + "\n")

                        if not result and self.exception:
                            f.write(f"\nFINAL STATUS: FAILED\nError: {str(self.exception)}\n")
                        else:
                            f.write(f"\nFINAL STATUS: SUCCESS\n")

                    log_step(self, self.tr("LOG FILE WRITTEN"), self.log_filename, "info")

                except Exception as log_error:
                    QgsMessageLog.logMessage(
                        f"Failed to write log file {self.log_filename}: {log_error}",
                        "MyLiDAR", Qgis.Warning
                    )

        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# ---------------------------------------------
# --- Main Vegetation Classification Method ---
# ---------------------------------------------

def _classify_vegetation_accepted(self):
    dialog = self.dialog

    # Step 1: Select input/output file path and parameters via dialog
    input_filename, output_filename = dialog.get_input_output()
    if not input_filename:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Input Selected"),
            self.tr("Please select a LiDAR layer or file.")
        )
        return

    if not output_filename:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Output Selected"),
            self.tr("Please specify an output file path.")
        )
        return
    
    log_filename = dialog.get_log_path()

    # Step 2: Get thresholds
    low_thresh, high_thresh, grass_enabled = dialog.get_values()

    # Step 3: Create and run the background task
    task_desc = f"{self.tr('Classifying vegetation in')} {os.path.basename(input_filename)}"
    task = VegetationClassificationTask(task_desc, input_filename, output_filename, low_thresh, high_thresh, grass_enabled, self, self.tr, log_filename)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Classifying vegetation in the background"),
        level=Qgis.Info,
        duration=-1
    )

def classify_vegetation(self):
    self.dialog = VegetationClassificationDialog(self.iface.mainWindow(), translator=self.tr)
    self.dialog.accepted.connect(lambda: _classify_vegetation_accepted(self))
    self.dialog.show()
    self.dialog.raise_()
    self.dialog.activateWindow()
