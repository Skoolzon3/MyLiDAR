# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QDialog
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from qgis.core import QgsPointCloudLayer, QgsProject

# --- Method-specific imports ---
from scipy.spatial import cKDTree

# --- Dialog imports ---
from .outlier_removal_dialog import OutlierRemovalDialog
from ...utils import create_loading_dialog

# -----------------------
# --- Outlier Removal ---
# -----------------------
# Description:
# This function removes outliers from a LiDAR file based on a specified radius and minimum number of neighbors.
# It uses a KD-tree during neighbor searching and allows the user to save the processed file.
# -----------------------

def remove_outliers(self):
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File to Clean',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not filename:
        return

    dialog = OutlierRemovalDialog(self.iface.mainWindow())
    if dialog.exec_() != QDialog.Accepted:
        return

    radius, min_neighbors = dialog.get_values()
    loading_dialog = create_loading_dialog(self, message="Processing LiDAR file...")

    try:
        QApplication.setOverrideCursor(Qt.WaitCursor)

        loading_dialog.show()
        QApplication.processEvents()
        QTest.qWait(100)

        las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

        # Obtain coordinates and build a KD-tree for neighbor search
        coords = np.vstack((las.x, las.y, las.z)).T
        tree = cKDTree(coords)
        neighbor_counts = tree.query_ball_point(coords, r=radius, return_length=True)
        mask = neighbor_counts >= min_neighbors

        # Create a mask for points with enough neighbors (min_neighbors)
        num_removed = np.sum(~mask)
        num_remaining = np.sum(mask)

        if num_remaining == 0:
            raise ValueError("All points were classified as outliers — no data would remain.")

        new_header = las.header.copy()
        las_filtered = laspy.LasData(new_header)

        # Filter points based on the mask
        filtered_coords = coords[mask]

        # Update header with new bounds
        las_filtered.header.min = [
            filtered_coords[:, 0].min(),
            filtered_coords[:, 1].min(),
            filtered_coords[:, 2].min()
        ]
        las_filtered.header.max = [
            filtered_coords[:, 0].max(),
            filtered_coords[:, 1].max(),
            filtered_coords[:, 2].max()
        ]
        las_filtered.points = las.points[mask]

        assert len(las_filtered.points) == np.sum(mask)

        output_path, _ = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            'Save Cleaned LiDAR File',
            os.path.splitext(filename)[0] + '_cleaned.laz',
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
            "Outlier Removal Complete",
            f"Removed {num_removed:,} outlier points.\n"
            f"Remaining: {num_remaining:,} points\n\n"
            f"Filtered file saved to:\n{output_path}"
        )

    except Exception as e:
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Error Removing Outliers",
            f"An error occurred:\n{e}"
        )

    finally:
        loading_dialog.close()
        QApplication.restoreOverrideCursor()
