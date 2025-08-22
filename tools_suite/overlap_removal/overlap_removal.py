# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from qgis.core import QgsPointCloudLayer, QgsProject

# --- Dialog imports ---
from ...utils import create_loading_dialog

# -----------------------
# --- Overlap Removal ---
# -----------------------
# Description:
# This function removes overlap points from a LiDAR file based on classification codes, by
# filting out points classified as overlap and saving the remaining points to a new point cloud.
# -----------------------

def remove_overlap(self):
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File to Remove Overlap Points',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not filename:
        return

    loading_dialog = create_loading_dialog(self, message="Removing overlapping points...")

    try:
        QApplication.setOverrideCursor(Qt.WaitCursor)

        loading_dialog.show()
        QApplication.processEvents()

        las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

        # Identify overlap points based on classification
        overlap_classes = {12, 17}  # Overlap classification codes
        classifications = las.classification
        is_non_overlap = ~np.isin(classifications, list(overlap_classes))

        # Filter only non-overlap points
        non_overlap_indices = np.where(is_non_overlap)[0]

        # Create a new LasData object with only non-overlap points
        new_header = las.header.copy()
        las_filtered = laspy.LasData(new_header)
        las_filtered.points = las.points[non_overlap_indices]

        x = las.x[non_overlap_indices]
        y = las.y[non_overlap_indices]
        z = las.z[non_overlap_indices]

        las_filtered.header.min = [x.min(), y.min(), z.min()]
        las_filtered.header.max = [x.max(), y.max(), z.max()]

        output_path, _ = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            'Save Non-Overlap LiDAR File',
            os.path.splitext(filename)[0] + '_non_overlap.laz',
            'LiDAR Files (*.las *.laz)'
        )
        if not output_path:
            return

        las_filtered.write(output_path)

        layer_name = os.path.splitext(os.path.basename(output_path))[0]
        pc_layer = QgsPointCloudLayer(output_path, layer_name, "pdal")
        if pc_layer.isValid():
            QgsProject.instance().addMapLayer(pc_layer)
        else:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Layer Load Warning",
                "The LiDAR file was saved but could not be loaded into QGIS."
            )

        QMessageBox.information(
            self.iface.mainWindow(),
            "Overlap Removal Complete",
            f"Original points: {len(las.points):,}\n"
            f"Overlap points removed: {np.sum(~is_non_overlap):,}\n"
            f"Remaining points: {len(non_overlap_indices):,}\n\n"
            f"Filtered file saved to:\n{output_path}"
        )

    except Exception as e:
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Error During Overlap Removal",
            f"An error occurred:\n{e}"
        )

    finally:
        loading_dialog.close()
        QApplication.restoreOverrideCursor()
