# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from qgis.core import QgsApplication, QgsPointCloudLayer, QgsProject, QgsTask, Qgis, QgsMessageLog, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QDateTime

# --- Dialog imports ---
from .point_filtering_dialog import PointFilteringDialog

# -----------------------
# --- Point Filtering ---
# --------------------------------------------------------------------------------------------
# Description:
# This module filters LiDAR points based on their classification codes. The user can select one
# or more classification values and choose whether to keep or remove the selected classes. The
# resulting filtered point cloud is written to a new LAS/LAZ file.
# --------------------------------------------------------------------------------------------

# -------------------------------------------
# --- Background Task for Point Filtering ---
# -------------------------------------------

class FilterPointsTask(QgsTask):
    """Filters points from a LiDAR file based on classification codes"""

    def __init__(self, description, input_filename, output_filename, selected_classes, parent, translator, log_filename=None):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.selected_classes = selected_classes
        self.parent = parent
        self.tr = translator
        self.exception = None
        self.num_removed = 0
        self.num_remaining = 0
        self.output_crs = None
        self.log_filename = log_filename
        self.log_entries = []

    def log_step(self, step_name, details="", relevancy="INFO"):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        levels = {
            "INFO": (Qgis.Info, self.tr("INFO")),
            "WARNING": (Qgis.Warning, self.tr("WARNING")),
            "CRITICAL": (Qgis.Critical, self.tr("CRITICAL"))
        }
        level = levels.get(relevancy, levels["INFO"])
        entry = f"[{timestamp}] {level[1]}  {step_name}: {details}"
        self.log_entries.append(entry)
        QgsMessageLog.logMessage(f"{step_name}: {details}", "MyLiDAR", level[0])

    def run(self):
        try:
            self.log_step(self.tr("PROCESS START"), f"Input: {os.path.basename(self.input_filename)}, Classes: {self.selected_classes}", "INFO")

            # Step 1: Read input file
            self.log_step(self.tr("READING INPUT FILE"), self.input_filename, "INFO")
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            pycrs = las.header.parse_crs(prefer_wkt=True)
            if pycrs:
                self.output_crs = QgsCoordinateReferenceSystem(pycrs.to_wkt())
                self.log_step(self.tr("CRS DETECTED"), f"From file header: {self.output_crs.authid()}", "INFO")
            else:
                self.log_step(self.tr("CRS NOT FOUND"), self.tr("No CRS found in file header. Checking input layer loaded in QGIS"), "WARNING")

                matched_layer = None
                for lyr in QgsProject.instance().mapLayers().values():
                    if isinstance(lyr, QgsPointCloudLayer) and lyr.source() == self.input_filename:
                        matched_layer = lyr
                        break

                if matched_layer:
                    if matched_layer.crs().isValid():
                        self.output_crs = matched_layer.crs()
                        self.log_step(self.tr("CRS ASSIGNED"), f"{self.tr('Using CRS assigned in QGIS')}: {self.output_crs.authid()}", "INFO")

                    else:
                        self.log_step(self.tr("INVALID CRS"), self.tr("Matched layer CRS is invalid, no CRS will be assigned"), "WARNING")

                else:
                    self.log_step(self.tr("NO LAYER MATCH"), self.tr("Input file not found among loaded layers. Cannot import CRS from QGIS"), "WARNING")

            self.log_step("CLASSIFICATION FILTERING", f"Total classifications: {len(las.classification)}, Target classes: {self.selected_classes}", "INFO")
            classifications = las.classification
            self.setProgress(10)

            mask = ~np.isin(classifications, self.selected_classes)

            self.num_removed = np.sum(~mask)
            self.num_remaining = np.sum(mask)
            self.log_step("FILTERING RESULTS", f"Removed: {self.num_removed:,}, Remaining: {self.num_remaining:,}", "INFO")

            if self.num_remaining == 0:
                error_msg = self.tr("No points remain after filtering.")
                self.log_step("FILTERING FAILED", error_msg, "CRITICAL")
                raise ValueError(error_msg)

            self.setProgress(60)

            self.log_step(self.tr("CREATING FILTERED LAS FILE"), f"Copying {self.num_remaining:,} points to new header", "INFO")
            new_header = las.header.copy()
            las_filtered = laspy.LasData(new_header)
            las_filtered.points = las.points[mask]
            las_filtered.update_header()

            self.log_step(self.tr("WRITING OUTPUT FILE"), self.output_filename, "INFO")
            las_filtered.write(self.output_filename)
            self.log_step("FILE WRITE COMPLETE", f"Filtered LAS saved successfully", "INFO")
            self.setProgress(100)

            self.log_step(self.tr("PROCESS COMPLETE"), f"Successfully filtered {self.num_remaining:,}/{self.num_removed + self.num_remaining:,} points", "INFO")
            return True

        except Exception as e:
            self.log_step(self.tr("PROCESS FAILED"), f"Exception: {str(e)}", "CRITICAL")
            self.exception = e
            return False

    def finished(self, result):
        try:
            if result:
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Point Filtering Complete"),
                    f"{self.tr('Filtered points')}: {self.num_removed:,}\n"
                    f"{self.tr('Remaining points')}: {self.num_remaining:,}\n\n"
                    f"{self.tr('Filtered file saved to')}:\n{self.output_filename}"
                )

                layer_name = os.path.splitext(os.path.basename(self.output_filename))[0]
                pc_layer = QgsPointCloudLayer(self.output_filename, layer_name, "pdal")
                if pc_layer.isValid():
                    if self.output_crs and self.output_crs.isValid():
                        pc_layer.setCrs(self.output_crs)
                        self.log_step(self.tr("LAYER CRS APPLIED"), f"{self.tr('Output layer CRS applied')}: {self.output_crs.authid()}", "INFO")
                    else:
                        self.log_step(self.tr("NO CRS FOR LAYER"), self.tr("No valid CRS available to assign to the output layer"), "WARNING")
                    QgsProject.instance().addMapLayer(pc_layer)
                    self.log_step(self.tr("LAYER ADDED TO PROJECT"), layer_name, "INFO")
                else:
                    self.log_step(self.tr("LAYER LOAD FAILED"), self.tr("The LiDAR file was saved but could not be loaded into QGIS"), "WARNING")

            else:
                if self.exception:
                    self.log_step(self.tr("ERROR EXCEPTION"), f"{self.tr('An error occurred during point filtering')}: {self.exception}", "CRITICAL")
                    QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error Filtering Points"), f"{self.tr('An error occurred')}:\n{self.exception}")
                else:
                    self.log_step(self.tr("TASK CANCELED"), self.tr('Point filtering was canceled by the user'), "INFO")

            if self.log_filename:
                try:
                    with open(self.log_filename, 'w', encoding='utf-8') as f:
                        f.write(f"MyLiDAR POINT FILTERING REPORT\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(f"Input file: {self.input_filename}\n")
                        f.write(f"Output file: {self.output_filename}\n")
                        f.write(f"Filter classes: {self.selected_classes}\n")
                        f.write(f"CRS: {self.output_crs.authid() if self.output_crs else 'Not set'}\n")
                        f.write(f"Total points processed: {self.num_removed + self.num_remaining:,}\n")
                        f.write(f"Points removed: {self.num_removed:,} ({100*self.num_removed/(self.num_removed + self.num_remaining):.1f}%)\n")
                        f.write(f"Points remaining: {self.num_remaining:,}\n\n")
                        f.write("PROCESSING STEPS:\n")
                        f.write("-" * 30 + "\n")
                        for entry in self.log_entries:
                            f.write(entry + "\n")

                        if not result and self.exception:
                            f.write(f"\nFINAL STATUS: FAILED\nError: {str(self.exception)}\n")
                        else:
                            f.write(f"\nFINAL STATUS: SUCCESS\n")

                    self.log_step(self.tr("LOG FILE WRITTEN"), self.log_filename, "INFO")

                except Exception as log_error:
                    QgsMessageLog.logMessage(
                        f"Failed to write log file {self.log_filename}: {log_error}",
                        "MyLiDAR", Qgis.Warning
                    )
        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# -----------------------------------
# --- Main Point Filtering Method ---
# -----------------------------------

def filter_points(self):
    # Step 1: Select input/output file path and parameters via dialog
    dialog = PointFilteringDialog(self.iface.mainWindow(), translator=self.tr)
    if dialog.exec() != QDialog.accepted:
        return

    input_filename, output_filename = dialog.get_input_output()
    selected_classes = dialog.get_filter_settings()
    log_filename = dialog.get_log_path()

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

    if not selected_classes:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Classes Selected"),
            self.tr("Please choose at least one classification code.")
        )
        return

    # Step 2: Create background task
    desc = f"{self.tr('Filtering points from')} {os.path.basename(input_filename)}"
    task = FilterPointsTask(desc, input_filename, output_filename, selected_classes, self, self.tr, log_filename)
    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Filtering points in the background"),
        level=Qgis.Info,
        duration=-1
    )
