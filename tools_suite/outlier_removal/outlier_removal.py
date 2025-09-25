# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QDialog
from qgis.core import QgsApplication, QgsPointCloudLayer, QgsProject, QgsTask, Qgis, QgsMessageLog

# --- Method-specific imports ---
from scipy.spatial import cKDTree

# --- Dialog imports ---
from .outlier_removal_dialog import OutlierRemovalDialog

# -----------------------
# --- Outlier Removal ---
# -----------------------
# Description:
# This function removes outliers from a LiDAR file based on a specified radius and minimum number of neighbors.
# It uses a KD-tree during neighbor searching and allows the user to save the processed file.
# -----------------------

# -------------------------------------------
# --- Background Task for Outlier Removal ---
# -------------------------------------------

class RemoveOutliersTask(QgsTask):
    """Remove outlier points from a LiDAR file in a background thread"""

    def __init__(self, description, input_filename, output_filename, radius, min_neighbors, parent):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.radius = radius
        self.min_neighbors = min_neighbors
        self.parent = parent
        self.exception = None
        self.num_removed = 0
        self.num_remaining = 0

    def run(self):
        try:
            # Step 1: Read the input file
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)

            # Step 2: Build KD-tree and find outliers
            coords = np.vstack((las.x, las.y, las.z)).T
            tree = cKDTree(coords)
            neighbor_counts = tree.query_ball_point(coords, r=self.radius, return_length=True)
            mask = neighbor_counts >= self.min_neighbors

            self.num_removed = np.sum(~mask)
            self.num_remaining = np.sum(mask)

            # Periodically check if the user has canceled the task
            if self.isCanceled():
                return False

            if self.num_remaining == 0:
                raise ValueError("All points were classified as outliers. No data would remain.")

            # Step 3: Create a new LasData object with the filtered points
            new_header = las.header.copy()
            las_filtered = laspy.LasData(new_header)
            las_filtered.points = las.points[mask]

            # Recalculate the header extents
            filtered_coords = coords[mask]
            las_filtered.header.min = [np.min(filtered_coords[:, 0]), np.min(filtered_coords[:, 1]), np.min(filtered_coords[:, 2])]
            las_filtered.header.max = [np.max(filtered_coords[:, 0]), np.max(filtered_coords[:, 1]), np.max(filtered_coords[:, 2])]

            # Step 4: Write the new file to the output path
            las_filtered.write(self.output_filename)

            return True  # Success
        except Exception as e:
            self.exception = e
            return False  # Failure

    def finished(self, result):
        try:
            if result:
                # Task completed successfully
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    "Outlier Removal Complete",
                    f"Removed {self.num_removed:,} outlier points.\n"
                    f"Remaining: {self.num_remaining:,} points\n\n"
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
                    QgsMessageLog.logMessage(f"An error occurred during outlier removal: {self.exception}", 'MyPlugin', Qgis.Critical)
                    QMessageBox.critical(self.parent.iface.mainWindow(), "Error Removing Outliers", f"An error occurred:\n{self.exception}")
                else:
                    QgsMessageLog.logMessage('Outlier removal was canceled by the user.', 'MyPlugin', Qgis.Info)
        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# -----------------------------------
# --- Main Outlier Removal Method ---
# -----------------------------------

def remove_outliers(self):
    # Step 1: Select input file path
    input_filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File to Clean',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not input_filename:
        return

    # Step 2: Get parameters via a custom dialog
    dialog = OutlierRemovalDialog(self.iface.mainWindow())
    if dialog.exec_() != QDialog.Accepted:
        return
    radius, min_neighbors = dialog.get_values()

    # Step 3: Select output file path
    default_output = os.path.splitext(input_filename)[0] + '_cleaned.laz'
    output_filename, _ = QFileDialog.getSaveFileName(
        self.iface.mainWindow(),
        'Save Cleaned LiDAR File',
        default_output,
        'LiDAR Files (*.las *.laz)'
    )
    if not output_filename:
        return

    # Step 4: Create and run the background task
    task_description = f"Removing outliers from {os.path.basename(input_filename)}"
    task = RemoveOutliersTask(task_description, input_filename, output_filename, radius, min_neighbors,self)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        "Task Started",
        "Removing outliers in the background.",
        level=Qgis.Info,
        duration=-1
    )
