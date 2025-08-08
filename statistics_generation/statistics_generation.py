from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

import laspy
from laspy import LazBackend
import matplotlib.pyplot as plt
import numpy as np

from ..utils import create_loading_dialog

# -----------------------------
# --- Statistics Generation ---
# -----------------------------

def generate_statistics(self):
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File to Analyze',
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

        # Classification values
        classifications = las.classification
        unique_classes, class_counts = np.unique(classifications, return_counts=True)
        classification_info = {
            0: ("Created, Never Classified", "#A0A0A0"), 1: ("Unclassified", "#B0B0B0"),
            2: ("Ground", "#8B4513"), 3: ("Low Vegetation", "#ADFF2F"),
            4: ("Medium Vegetation", "#32CD32"), 5: ("High Vegetation", "#006400"),
            6: ("Building", "#FF4500"), 7: ("Low Point (Noise)", "#D3D3D3"),
            8: ("Model Key-point", "#FFD700"), 9: ("Water", "#1E90FF"),
            10: ("Rail", "#8B0000"), 11: ("Road Surface", "#A0522D"),
            12: ("Overlap", "#C0C0C0"), 13: ("Wire Guard", "#00CED1"),
            14: ("Wire Conductor", "#20B2AA"), 15: ("Transmission Tower", "#000080"),
            16: ("Wire-structure Connector", "#708090"), 17: ("Bridge Deck", "#A9A9A9"),
            18: ("High Noise", "#800080")
        }

        labels = [classification_info.get(c, (f"Class {c}", "#CCCCCC"))[0] for c in unique_classes]
        colors = [classification_info.get(c, ("Unknown", "#CCCCCC"))[1] for c in unique_classes]
        plt.figure(figsize=(8, 8))
        plt.pie(
            class_counts,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=140
        )
        plt.title("Classification Distribution", fontweight='bold')
        plt.gcf().canvas.manager.set_window_title("Classification Distribution")
        plt.tight_layout()
        plt.show()

        # Return Number
        return_numbers = las.return_number
        unique_returns, return_counts = np.unique(return_numbers, return_counts=True)
        return_labels = [f"Return {r}" for r in unique_returns]

        plt.figure(figsize=(6, 4))
        plt.bar(return_labels, return_counts, color='lightgreen')
        plt.title("Return Number Distribution", fontweight='bold')
        plt.gcf().canvas.manager.set_window_title("Return Number Distribution")
        plt.xlabel("Return Number")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.show()

        # Point Density
        x = las.x
        y = las.y

        plt.figure(figsize=(6, 5))
        plt.hist2d(x, y, bins=100, cmap='viridis')
        plt.title("Point Density Distribution", fontweight='bold')
        plt.gcf().canvas.manager.set_window_title("Point Density Distribution")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.colorbar(label="Point Count")
        plt.tight_layout()
        plt.show()

    except Exception as e:
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Error Generating Statistics",
            f"An error occurred:\n{e}"
        )

    finally:
        loading_dialog.close()
        QApplication.restoreOverrideCursor()
