from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

import laspy
from laspy import LazBackend
import numpy as np
from sklearn.cluster import DBSCAN

from .utils import create_loading_dialog
from .building_count_dialog import BuildingParamsDialog

# ---------------------
# --- Builing Count ---
# ---------------------

def count_buildings(self):
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File to Count Buildings',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not filename:
        return

    param_dialog = BuildingParamsDialog(self.iface.mainWindow())
    if not param_dialog.exec_():
        return

    eps, min_samples = param_dialog.get_params()

    loading_dialog = create_loading_dialog(self)

    try:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        loading_dialog.show()
        QApplication.processEvents()
        QTest.qWait(100)

        las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

        # Filter building-classified points
        building_class_code = 6
        classifications = las.classification
        is_building = classifications == building_class_code

        if np.sum(is_building) == 0:
            QMessageBox.information(
                self.iface.mainWindow(),
                "No Buildings Found",
                "No buildings were found in this file."
            )
            return

        # Extract X and Y for clustering
        coords = np.vstack((las.x[is_building], las.y[is_building])).T

        # DBSCAN clustering
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
        labels = db.labels_

        # Count clusters (excluding noise points labeled -1)
        num_buildings = len(set(labels)) - (1 if -1 in labels else 0)

        QMessageBox.information(
            self.iface.mainWindow(),
            "Building Detection Complete",
            f"Building points detected: {np.sum(is_building):,}\n"
            f"Approximate number of building detected: {num_buildings:,}"
        )

    except Exception as e:
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Error Detecting Buildings",
            f"An error occurred:\n{e}"
        )

    finally:
        loading_dialog.close()
        QApplication.restoreOverrideCursor()
