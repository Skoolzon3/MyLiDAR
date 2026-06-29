# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsApplication, QgsPointCloudLayer, QgsProject, QgsTask, Qgis, QgsMessageLog, QgsCoordinateReferenceSystem

# --- Dialog imports ---
from .point_filtering_dialog import PointFilteringDialog

# --- Utility imports ---
from ..utils import log_step

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

    def run(self):
        try:
            log_step(self, self.tr("PROCESS START"), f"Input: {os.path.basename(self.input_filename)}, Classes: {self.selected_classes}", "info")

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

            log_step(self, self.tr("CLASSIFICATION FILTERING"), f"Total classifications: {len(las.classification)}, Target classes: {self.selected_classes}", "info")
            classifications = las.classification
            self.setProgress(10)

            mask = ~np.isin(classifications, self.selected_classes)

            self.num_removed = np.sum(~mask)
            self.num_remaining = np.sum(mask)
            log_step(self, self.tr("FILTERING RESULTS"), f"Removed: {self.num_removed:,}, Remaining: {self.num_remaining:,}", "info")

            if self.num_remaining == 0:
                error_msg = self.tr("No points remain after filtering.")
                log_step(self, self.tr("FILTERING FAILED"), error_msg, "critical")
                raise ValueError(error_msg)

            self.setProgress(60)

            log_step(self, self.tr("CREATING FILTERED LAS FILE"), f"Copying {self.num_remaining:,} points to new header", "info")
            new_header = las.header.copy()
            las_filtered = laspy.LasData(new_header)
            las_filtered.points = las.points[mask]
            las_filtered.update_header()

            log_step(self, self.tr("WRITING OUTPUT FILE"), self.output_filename, "info")
            las_filtered.write(self.output_filename)
            log_step(self, self.tr("FILE WRITE COMPLETE"), f"Filtered LAS saved successfully", "info")
            self.setProgress(100)

            log_step(self, self.tr("PROCESS COMPLETE"), f"Successfully filtered {self.num_remaining:,}/{self.num_removed + self.num_remaining:,} points", "info")
            return True

        except Exception as e:
            log_step(self, self.tr("PROCESS FAILED"), f"Exception: {str(e)}", "critical")
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
                        log_step(self, self.tr("LAYER CRS APPLIED"), f"{self.tr('Output layer CRS applied')}: {self.output_crs.authid()}", "info")
                    else:
                        log_step(self, self.tr("NO CRS FOR LAYER"), self.tr("No valid CRS available to assign to the output layer"), "warning")
                    QgsProject.instance().addMapLayer(pc_layer)
                    log_step(self, self.tr("LAYER ADDED TO PROJECT"), layer_name, "info")
                else:
                    log_step(self, self.tr("LAYER LOAD FAILED"), self.tr("The LiDAR file was saved but could not be loaded into QGIS"), "warning")

            else:
                if self.exception:
                    log_step(self, self.tr("ERROR EXCEPTION"), f"{self.tr('An error occurred during point filtering')}: {self.exception}", "critical")
                    QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error Filtering Points"), f"{self.tr('An error occurred')}:\n{self.exception}")
                else:
                    log_step(self, self.tr("TASK CANCELED"), self.tr('Point filtering was canceled by the user'), "info")

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

                    log_step(self, self.tr("LOG FILE WRITTEN"), self.log_filename, "info")

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

def _filter_points_accepted(self):
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

    selected_classes = dialog.get_filter_settings()
    if not selected_classes:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Classes Selected"),
            self.tr("Please choose at least one classification code.")
        )
        return
    
    log_filename = dialog.get_log_path()

    # Step 2: Create and run the background task
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

def filter_points(self):
    self.dialog = PointFilteringDialog(self.iface.mainWindow(), translator=self.tr)
    self.dialog.accepted.connect(lambda: _filter_points_accepted(self))
    self.dialog.show()
    self.dialog.raise_()
    self.dialog.activateWindow()
