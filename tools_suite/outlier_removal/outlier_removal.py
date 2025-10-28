# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from qgis.core import QgsApplication, QgsPointCloudLayer, QgsProject, QgsTask, Qgis, QgsMessageLog

# --- Method-specific imports ---
from scipy.spatial import cKDTree

# --- Dialog imports ---
from .outlier_removal_dialog import OutlierRemovalDialog

# -----------------------
# --- Outlier Removal ---
# --------------------------------------------------------------------------------------------
# Description:
# This function removes outliers from a LiDAR file based on a specified radius and minimum
# number of neighbors. It uses a KD-tree during neighbor searching and allows the user to save
# the processed file.
# --------------------------------------------------------------------------------------------

# -------------------------------------------
# --- Background Task for Outlier Removal ---
# -------------------------------------------

class RemoveOutliersTask(QgsTask):
    """Remove outlier points from a LiDAR file in a background thread"""

    def __init__(self, description, input_filename, output_filename, radius, min_neighbors, parent, translator):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.radius = radius
        self.min_neighbors = min_neighbors
        self.parent = parent
        self.exception = None
        self.tr = translator
        self.num_removed = 0
        self.num_remaining = 0

    def run(self):
        try:
            # Step 1: Read input file
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            self.setProgress(10)

            # Step 2: Build KD-tree
            coords = np.vstack((las.x, las.y, las.z)).T
            tree = cKDTree(coords)
            self.setProgress(20)

            # Step 3: Find outliers
            n_points = coords.shape[0]
            batch_size = max(10000, n_points // 100)  # ~100 updates
            neighbor_counts = np.empty(n_points, dtype=np.int32)

            for i in range(0, n_points, batch_size):
                if self.isCanceled():
                    return False

                j = min(i + batch_size, n_points)
                neighbor_counts[i:j] = tree.query_ball_point(coords[i:j], r=self.radius, return_length=True)

                progress = 20 + (70 * j / n_points) # Progress updated proportionally (20–90%)
                self.setProgress(progress)

            # Step 4: Build mask
            mask = neighbor_counts >= self.min_neighbors
            self.num_removed = np.sum(~mask)
            self.num_remaining = np.sum(mask)

            if self.num_remaining == 0:
                raise ValueError(self.tr("All points were classified as outliers. No data would remain"))

            # Step 3: Create new LasData object with the filtered points
            new_header = las.header.copy()
            las_filtered = laspy.LasData(new_header)
            las_filtered.points = las.points[mask]

            # Recalculate the header extents
            filtered_coords = coords[mask]
            las_filtered.header.min = [np.min(filtered_coords[:, 0]), np.min(filtered_coords[:, 1]), np.min(filtered_coords[:, 2])]
            las_filtered.header.max = [np.max(filtered_coords[:, 0]), np.max(filtered_coords[:, 1]), np.max(filtered_coords[:, 2])]

            # Step 4: Write new file to the output path
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
                    self.tr("Outlier Removal Complete"),
                    f"{self.tr('Removed outlier points')}: {self.num_removed:,}\n"
                    f"{self.tr('Remaining points')}: {self.num_remaining:,}\n\n"
                    f"{self.tr('Filtered file saved to')}:\n{self.output_filename}"
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
                    QgsMessageLog.logMessage(f"{self.tr('An error occurred during outlier removal')}: {self.exception}", 'MyLiDAR', Qgis.Critical)
                    QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error Removing Outliers"), f"{self.tr('An error occurred')}:\n{self.exception}")
                else:
                    QgsMessageLog.logMessage(self.tr('Outlier removal was canceled by the user'), 'MyLiDAR', Qgis.Info)
        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# -----------------------------------
# --- Main Outlier Removal Method ---
# -----------------------------------

def remove_outliers(self):
    # Step 1: Select input file path and parameters via dialog
    dialog = OutlierRemovalDialog(self.iface.mainWindow(), translator=self.tr)
    if dialog.exec_() != QDialog.Accepted:
        return

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

    radius, min_neighbors = dialog.get_values()

    # Step 2: Create and run the background task
    task_description = f"{self.tr('Removing outliers from')} {os.path.basename(input_filename)}"
    task = RemoveOutliersTask(task_description, input_filename, output_filename, radius, min_neighbors,self, self.tr)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Removing outliers in the background"),
        level=Qgis.Info,
        duration=-1
    )
