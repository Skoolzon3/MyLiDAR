import os

from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QDialog
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtCore import Qt

import laspy
from laspy import LazBackend
import numpy as np
from scipy.spatial import cKDTree

from ..utils import create_loading_dialog
from .vegetation_classification_dialog import VegetationClassificationDialog

# ---------------------------------
# --- Vegetation Classification ---
# ---------------------------------

def classify_vegetation(self):
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File to Classify Vegetation',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not filename:
        return

    loading_dialog = create_loading_dialog(self)

    try:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        loading_dialog.show()
        QApplication.processEvents()

        las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

        # Standard ASPRS classes
        ground_class = 2
        low_class = 3
        medium_class = 4
        high_class = 5
        classifications = las.classification

        # Ground points
        ground_idx = np.where(classifications == ground_class)[0]
        if len(ground_idx) == 0:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "No Ground Points",
                "No ground points (class 2) found in the file. Cannot calculate vegetation height."
            )
            return

        ground_xy = np.vstack((las.x[ground_idx], las.y[ground_idx])).T
        ground_z = las.z[ground_idx]

        # Tree points originally marked as high vegetation
        high_veg_idx = np.where(classifications == high_class)[0]
        if len(high_veg_idx) == 0:
            QMessageBox.information(
                self.iface.mainWindow(),
                "No High Vegetation Points",
                "No high vegetation points (class 5) found in the selected file."
            )
            return

        veg_xy = np.vstack((las.x[high_veg_idx], las.y[high_veg_idx])).T
        veg_z = las.z[high_veg_idx]

        # Interpolate local ground height using nearest neighbor
        tree = cKDTree(ground_xy)
        dist, nearest_ground_idx = tree.query(veg_xy, k=1)
        local_ground_z = ground_z[nearest_ground_idx]

        # Vegetation height above ground
        veg_height = veg_z - local_ground_z

        # Ask user for thresholds
        dlg = VegetationClassificationDialog(self.iface.mainWindow())
        if dlg.exec_() != QDialog.Accepted:
            return
        low_thresh, high_thresh = dlg.get_values()


        low_mask = veg_height < low_thresh
        medium_mask = (veg_height >= low_thresh) & (veg_height <= high_thresh)
        high_mask = veg_height > high_thresh

        # Reclassify vegetation
        las.classification[high_veg_idx[low_mask]] = low_class
        las.classification[high_veg_idx[medium_mask]] = medium_class
        las.classification[high_veg_idx[high_mask]] = high_class

        output_path, _ = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            'Save Reclassified Vegetation File',
            os.path.splitext(filename)[0] + '_classified_vegetation.laz',
            'LiDAR Files (*.las *.laz)'
        )
        if not output_path:
            return

        las.write(output_path)

        QMessageBox.information(
            self.iface.mainWindow(),
            "Vegetation Reclassification Complete",
            f"Original high veg points: {len(high_veg_idx):,}\n"
            f"Low vegetation (<{low_thresh} m): {np.sum(low_mask):,}\n"
            f"Medium vegetation ({low_thresh}-{high_thresh} m): {np.sum(medium_mask):,}\n"
            f"High vegetation (>{high_thresh} m): {np.sum(high_mask):,}\n\n"
            f"Updated file saved to:\n{output_path}"
        )

    except Exception as e:
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Error During Classification",
            f"An error occurred:\n{e}"
        )

    finally:
        loading_dialog.close()
        QApplication.restoreOverrideCursor()
