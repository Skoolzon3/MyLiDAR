# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QDialog
from qgis.core import QgsPointCloudLayer, QgsProject, QgsTask, QgsApplication, Qgis, QgsMessageLog

# --- Method-specific imports ---
from scipy.spatial import cKDTree

# --- Dialog imports ---
from .vegetation_classification_dialog import VegetationClassificationDialog

# ---------------------------------
# --- Vegetation Classification ---
# ---------------------------------
# Description:
# This module classifies vegetation in LiDAR data into low, medium, and high categories,
# based on user-defined height thresholds.
# ---------------------------------

# -----------------------------------------------------
# --- Background Task for Vegetation Classification ---
# -----------------------------------------------------

class VegetationClassificationTask(QgsTask):
    """Background task for classifying LiDAR vegetation points"""

    def __init__(self, description, filename, output_path, low_thresh, high_thresh, parent):
        super().__init__(description, QgsTask.CanCancel)
        self.filename = filename
        self.output_path = output_path
        self.low_thresh = low_thresh
        self.high_thresh = high_thresh
        self.parent = parent

        self.exception = None
        self.stats = None

    def run(self):
        try:
            las = laspy.read(self.filename, laz_backend=LazBackend.Lazrs)

            # Standard ASPRS classes
            ground_class = 2
            low_class = 3
            medium_class = 4
            high_class = 5
            classifications = las.classification

            # --- Data Preparation ---

            # Ground points
            ground_idx = np.where(classifications == ground_class)[0]
            if len(ground_idx) == 0:
                raise ValueError("No ground points (class 2) found in the file.")

            ground_xy = np.vstack((las.x[ground_idx], las.y[ground_idx])).T
            ground_z = las.z[ground_idx]

            # Points originally marked as high vegetation
            high_veg_idx = np.where(classifications == high_class)[0]
            if len(high_veg_idx) == 0:
                raise ValueError("No high vegetation points (class 5) found in the file.")

            veg_xy = np.vstack((las.x[high_veg_idx], las.y[high_veg_idx])).T
            veg_z = las.z[high_veg_idx]

            # Interpolate local ground height using nearest neighbor
            tree = cKDTree(ground_xy)
            dist, nearest_ground_idx = tree.query(veg_xy, k=1)
            local_ground_z = ground_z[nearest_ground_idx]

            # Vegetation height above ground
            veg_height = veg_z - local_ground_z

            # ---------------------------------

            low_mask = veg_height < self.low_thresh
            medium_mask = (veg_height >= self.low_thresh) & (veg_height <= self.high_thresh)
            high_mask = veg_height > self.high_thresh

            # Reclassify vegetation
            las.classification[high_veg_idx[low_mask]] = low_class
            las.classification[high_veg_idx[medium_mask]] = medium_class
            las.classification[high_veg_idx[high_mask]] = high_class

            # Save file
            las.write(self.output_path)

            self.stats = {
                "num_high_orig": len(high_veg_idx),
                "num_low": int(np.sum(low_mask)),
                "num_medium": int(np.sum(medium_mask)),
                "num_high": int(np.sum(high_mask))
            }

            return True
        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        try:
            if result:
                layer_name = os.path.splitext(os.path.basename(self.output_path))[0]
                pc_layer = QgsPointCloudLayer(self.output_path, layer_name, "pdal")
                if pc_layer.isValid():
                    QgsProject.instance().addMapLayer(pc_layer)
                else:
                    QMessageBox.warning(
                        self.parent.iface.mainWindow(),
                        "Layer Load Warning",
                        "The LiDAR file was saved but could not be loaded into QGIS."
                    )

                s = self.stats
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    "Vegetation Reclassification Complete",
                    f"Original high veg points: {s['num_high_orig']:,}\n"
                    f"Low vegetation (<{self.low_thresh} m): {s['num_low']:,}\n"
                    f"Medium vegetation ({self.low_thresh}-{self.high_thresh} m): {s['num_medium']:,}\n"
                    f"High vegetation (>{self.high_thresh} m): {s['num_high']:,}\n\n"
                    f"Updated file saved to:\n{self.output_path}"
                )
            else:
                msg = f"An error occurred: {self.exception}" if self.exception else "Vegetation classification failed."
                QgsMessageLog.logMessage(msg, "MyPlugin", Qgis.Critical)
                QMessageBox.critical(self.parent.iface.mainWindow(), "Error During Classification", msg)
        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# ---------------------------------------------
# --- Main Vegetation Classification Method ---
# ---------------------------------------------

def classify_vegetation(self):
    # Step 1: Select input file path
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File to Classify Vegetation',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not filename:
        return

    # Step 2: Get thresholds
    dlg = VegetationClassificationDialog(self.iface.mainWindow())
    if dlg.exec_() != QDialog.Accepted:
        return
    low_thresh, high_thresh = dlg.get_values()

    # Step 3: Select output file path
    output_path, _ = QFileDialog.getSaveFileName(
        self.iface.mainWindow(),
        'Save Reclassified Vegetation File',
        os.path.splitext(filename)[0] + '_classified_vegetation.laz',
        'LiDAR Files (*.las *.laz)'
    )
    if not output_path:
        return

    # Step 4: Create and run the background task
    task_desc = f"Classifying vegetation in {os.path.basename(filename)}"
    task = VegetationClassificationTask(task_desc, filename, output_path, low_thresh, high_thresh, self)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        "Task Started",
        "Vegetation classification running in the background...",
        level=Qgis.Info,
        duration=-1
    )
