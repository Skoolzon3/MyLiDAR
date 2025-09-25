# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.core import QgsApplication, QgsPointCloudLayer, QgsProject, QgsTask, Qgis, QgsMessageLog

# -------------------------------------------
# --- Background Task for Overlap Removal ---
# -------------------------------------------

class RemoveOverlapTask(QgsTask):
    """Remove overlap points from a LiDAR file in a background thread"""

    def __init__(self, description, input_filename, output_filename, parent):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.parent = parent
        self.exception = None
        self.original_points_count = 0
        self.remaining_points_count = 0

    def run(self):
        try:
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            self.original_points_count = len(las.points)
            overlap_classes = {12, 17}
            is_non_overlap = ~np.isin(las.classification, list(overlap_classes))
            non_overlap_indices = np.where(is_non_overlap)[0]
            self.remaining_points_count = len(non_overlap_indices)

            if self.isCanceled():
                return False

            new_header = las.header.copy()
            las_filtered = laspy.LasData(new_header)
            las_filtered.points = las.points[non_overlap_indices]

            x, y, z = las_filtered.x, las_filtered.y, las_filtered.z
            las_filtered.header.min = [np.min(x), np.min(y), np.min(z)]
            las_filtered.header.max = [np.max(x), np.max(y), np.max(z)]
            las_filtered.write(self.output_filename)

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
                    "Overlap Removal Complete",
                    f"Original points: {self.original_points_count:,}\n"
                    f"Overlap points removed: {self.original_points_count - self.remaining_points_count:,}\n"
                    f"Remaining points: {self.remaining_points_count:,}\n\n"
                    f"Filtered file saved to:\n{self.output_filename}"
                )
                layer_name = os.path.splitext(os.path.basename(self.output_filename))[0]
                pc_layer = QgsPointCloudLayer(self.output_filename, layer_name, "pdal")
                if pc_layer.isValid():
                    QgsProject.instance().addMapLayer(pc_layer)
                else:
                    QMessageBox.warning(
                        self.parent.iface.mainWindow(),
                        "Layer Load Warning",
                        "The LiDAR file was saved but could not be loaded into QGIS."
                    )
            else:
                # Task failed / canceled
                if self.exception:
                    QgsMessageLog.logMessage(f"An error occurred: {self.exception}", 'MyPlugin', Qgis.Critical)
                    QMessageBox.critical(self.parent.iface.mainWindow(), "Error", f"An error occurred:\n{self.exception}")
                else:
                    QgsMessageLog.logMessage('Task was canceled.', 'MyPlugin', Qgis.Info)
        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# -----------------------
# --- Overlap Removal ---
# -----------------------
# Description:
# This function removes overlap points from a LiDAR file based on classification codes, by
# filting out points classified as overlap and saving the remaining points to a new point cloud.
# -----------------------

def remove_overlap(self):

    # Step 1: Get input file from user
    input_filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File to Remove Overlap Points',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not input_filename:
        return

    # Step 2: Get output file path from user
    default_output = os.path.splitext(input_filename)[0] + '_non_overlap.laz'
    output_filename, _ = QFileDialog.getSaveFileName(
        self.iface.mainWindow(),
        'Save Non-Overlap LiDAR File',
        default_output,
        'LiDAR Files (*.las *.laz)'
    )
    if not output_filename:
        return

    # Step 3: Create the background task
    task_description = f"Removing overlap from {os.path.basename(input_filename)}"
    task = RemoveOverlapTask(task_description, input_filename, output_filename, self)
    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)
