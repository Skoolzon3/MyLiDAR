# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from qgis.core import QgsApplication, QgsPointCloudLayer, QgsProject, QgsTask, Qgis, QgsMessageLog

# --- Dialog imports ---
from .overlap_removal_dialog import OverlapRemovalDialog

# -----------------------
# --- Overlap Removal ---
# ----------------------------------------------------------------------------------------------
# Description:
# This function removes overlap points from a LiDAR file based on classification codes, by
# filting out points classified as overlap and saving the remaining points to a new point cloud.
# ----------------------------------------------------------------------------------------------

# -------------------------------------------
# --- Background Task for Overlap Removal ---
# -------------------------------------------

class RemoveOverlapTask(QgsTask):
    """Remove overlap points from a LiDAR file in a background thread"""

    def __init__(self, description, input_filename, output_filename, parent, translator):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.parent = parent
        self.exception = None
        self.tr = translator
        self.original_points_count = 0
        self.remaining_points_count = 0

    def run(self):
        try:
            # Stage 1: Read input
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            self.original_points_count = len(las.points)
            self.setProgress(25)

            # Stage 2: Filter
            overlap_classes = {12, 17}
            is_non_overlap = ~np.isin(las.classification, list(overlap_classes))
            non_overlap_indices = np.where(is_non_overlap)[0]
            self.remaining_points_count = len(non_overlap_indices)
            self.setProgress(50)

            if self.isCanceled():
                return False

            # Stage 3: Create new LAS
            new_header = las.header.copy()
            las_filtered = laspy.LasData(new_header)
            las_filtered.points = las.points[non_overlap_indices]
            self.setProgress(75)

            # Stage 4: Update header & write
            x, y, z = las_filtered.x, las_filtered.y, las_filtered.z
            las_filtered.header.min = [np.min(x), np.min(y), np.min(z)]
            las_filtered.header.max = [np.max(x), np.max(y), np.max(z)]
            las_filtered.write(self.output_filename)
            self.setProgress(100)
            return True

        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        try:
            if result:
                # Task completed successfully
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Overlap Removal Complete"),
                    f"{self.tr('Original points')}: {self.original_points_count:,}\n"
                    f"{self.tr('Overlap points removed')}: {self.original_points_count - self.remaining_points_count:,}\n"
                    f"{self.tr('Remaining points')}: {self.remaining_points_count:,}\n\n"
                    f"{self.tr('Filtered file saved to')}: \n{self.output_filename}"
                )
                layer_name = os.path.splitext(os.path.basename(self.output_filename))[0]
                pc_layer = QgsPointCloudLayer(self.output_filename, layer_name, "pdal")
                if pc_layer.isValid():
                    QgsProject.instance().addMapLayer(pc_layer)
                else:
                    QMessageBox.warning(
                        self.parent.iface.mainWindow(),
                        self.tr("Layer Load Warning"),
                        self.tr("The LiDAR file was saved but could not be loaded into QGIS")
                    )
            else:
                # Task failed / canceled
                if self.exception:
                    QgsMessageLog.logMessage(f"{self.tr('An error occurred')}: {self.exception}", 'MyLiDAR', Qgis.Critical)

                    QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error"), f"{self.tr('An error occurred')}: \n{self.exception}")
                else:
                    QgsMessageLog.logMessage(self.tr('Task was canceled'), 'MyLiDAR', Qgis.Info)
        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# -----------------------------------
# --- Main Overlap Removal Method ---
# -----------------------------------

def remove_overlap(self):
    dlg = OverlapRemovalDialog(self.iface.mainWindow(), self.tr)
    if dlg.exec_() != QDialog.Accepted:
        return

    input_filename, output_filename = dlg.get_input_output()
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

    task_description = f"{self.tr('Removing overlap from')} {os.path.basename(input_filename)}"
    task = RemoveOverlapTask(task_description, input_filename, output_filename, self, self.tr)
    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Removing overlapping points in the background"),
        level=Qgis.Info,
        duration=-1
    )
