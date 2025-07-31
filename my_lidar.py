import os

# QGIS and PyQt imports
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QMenu
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# Backend imports
import laspy
from laspy import LazBackend

# Data handling imports
import numpy as np

# Spatial data handling imports
# from scipy.interpolate import griddata

# External utility functions
from .utils import create_loading_dialog

# --- Method imports ---
from .report_generation.report_generation import generate_report
from .outlier_removal.outlier_removal import remove_outliers
from .overlap_removal.overlap_removal import remove_overlap
from .building_count.building_count import count_buildings

# -----------------------------
# --- My LiDAR Plugin Class ---
# -----------------------------
class MyLiDARPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.secondary_action = None
        self.third_action = None
        self.fourth_action = None
        self.fifth_action = None

    def tr(self, message):
        return QCoreApplication.translate('LiDAR Document Generator', message)

    def initGui(self):
        report_icon_path = os.path.join(self.plugin_dir, 'icons/report.png')
        cleanup_icon_path = os.path.join(self.plugin_dir, 'icons/cleanup.png')
        overlap_icon_path = os.path.join(self.plugin_dir, 'icons/overlap.png')
        building_icon_path = os.path.join(self.plugin_dir, 'icons/building.png')
        vegetation_icon_path = os.path.join(self.plugin_dir, 'icons/vegetation.png')

        self.menu = QMenu(self.tr("MyLiDAR"), self.iface.mainWindow().menuBar())
        self.iface.mainWindow().menuBar().insertMenu(
            self.iface.mainWindow().menuBar().actions()[-1],  # Insert before "Help"
            self.menu
        )

        self.action = QAction(QIcon(report_icon_path), self.tr('Generate LiDAR File Report'), self.iface.mainWindow())
        self.action.triggered.connect(self.report_generation)
        self.iface.addToolBarIcon(self.action)
        self.menu.addAction(self.action)

        self.secondary_action = QAction(QIcon(cleanup_icon_path), self.tr('Remove outlier points'), self.iface.mainWindow())
        self.secondary_action.triggered.connect(self.outlier_removal)
        self.iface.addToolBarIcon(self.secondary_action)
        self.menu.addAction(self.secondary_action)

        self.third_action = QAction(QIcon(overlap_icon_path), self.tr('Remove overlapping'), self.iface.mainWindow())
        self.third_action.triggered.connect(self.overlap_removal)
        self.iface.addToolBarIcon(self.third_action)
        self.menu.addAction(self.third_action)

        # Toolbar-only actions
        self.fourth_action = QAction(QIcon(building_icon_path), self.tr('Count buildings'), self.iface.mainWindow())
        self.fourth_action.triggered.connect(self.building_count)
        self.menu.addAction(self.fourth_action)

        self.fifth_action = QAction(QIcon(vegetation_icon_path), self.tr('Classify vegetation'), self.iface.mainWindow())
        self.fifth_action.triggered.connect(self.classify_vegetation)
        self.menu.addAction(self.fifth_action)

    def unload(self):
        self.menu.removeAction(self.action)
        self.menu.removeAction(self.secondary_action)
        self.menu.removeAction(self.third_action)
        self.menu.removeAction(self.fourth_action)
        self.menu.removeAction(self.fifth_action)

        self.iface.removeToolBarIcon(self.action)
        self.iface.removeToolBarIcon(self.secondary_action)
        self.iface.removeToolBarIcon(self.third_action)
        self.iface.removeToolBarIcon(self.fourth_action)
        self.iface.removeToolBarIcon(self.fifth_action)

        self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())

    # --- Report Generation ---
    def report_generation(self):
        generate_report(self)

    # --- Outlier Removal ---
    def outlier_removal(self):
        remove_outliers(self)

    # --- Overlap Removal ---
    def overlap_removal(self):
        remove_overlap(self)

    # --- Builing Count ---
    def building_count(self):
        count_buildings(self)

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

            # Class codes
            low_class = 3
            medium_class = 4
            high_class = 5

            classifications = las.classification
            is_original = classifications == high_class
            original_indices = np.where(is_original)[0]

            if len(original_indices) == 0:
                QMessageBox.information(
                    self.iface.mainWindow(),
                    "No High Vegetation Points",
                    "No high vegetation points (classification code 5) found in the selected file."
                )
                return

            z_vals = np.asarray(las.z[original_indices])
            mean_z = z_vals.mean()
            delta = 2.0  # You can adjust this threshold buffer (in meters)

            # Classification based on thresholds
            low_mask = z_vals < (mean_z - delta)
            medium_mask = (z_vals >= (mean_z - delta)) & (z_vals <= (mean_z + delta))
            high_mask = z_vals > (mean_z + delta)

            las.classification[original_indices[low_mask]] = low_class
            las.classification[original_indices[medium_mask]] = medium_class
            las.classification[original_indices[high_mask]] = high_class  # Optionally redundant

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
                f"Original high veg points: {len(original_indices):,}\n"
                f"Mean height (Z): {mean_z:.2f} m\n"
                f"Threshold delta: ±{delta:.2f} m\n\n"
                f"Low vegetation (class 3): {np.sum(low_mask):,}\n"
                f"Medium vegetation (class 4): {np.sum(medium_mask):,}\n"
                f"High vegetation (class 5): {np.sum(high_mask):,}\n\n"
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


    # ----------------------------------------------
    # --- Vegetation Classification (normalized) ---
    # ----------------------------------------------
    # Currently disabled due to efficiency issues with large datasets

    # def classify_vegetation(self):
    #     filename, _ = QFileDialog.getOpenFileName(
    #         self.iface.mainWindow(),
    #         'Select LiDAR File to Classify Vegetation (Normalized)',
    #         '',
    #         'LiDAR Files (*.las *.laz)'
    #     )
    #     if not filename:
    #         return

    #     loading_dialog = create_loading_dialog(self)

    #     try:
    #         QApplication.setOverrideCursor(Qt.WaitCursor)

    #         loading_dialog.show()
    #         QApplication.processEvents()

    #         las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

    #         # --- Extract Ground Points ---
    #         ground_class_code = 2
    #         ground_mask = las.classification == ground_class_code

    #         if np.sum(ground_mask) < 3:
    #             QMessageBox.warning(
    #                 self.iface.mainWindow(),
    #                 "Insufficient Ground Points",
    #                 "Fewer than 3 ground points found — cannot interpolate terrain surface."
    #             )
    #             return

    #         ground_x = las.x[ground_mask]
    #         ground_y = las.y[ground_mask]
    #         ground_z = las.z[ground_mask]

    #         # --- Interpolate Ground Surface (DTM) ---
    #         all_x = las.x
    #         all_y = las.y

    #         terrain = griddata(
    #             points=(ground_x, ground_y),
    #             values=ground_z,
    #             xi=(all_x, all_y),
    #             method='linear'
    #         )

    #         if np.any(np.isnan(terrain)):
    #             QMessageBox.warning(
    #                 self.iface.mainWindow(),
    #                 "Interpolation Error",
    #                 "Some terrain heights could not be interpolated. Consider using denser ground points."
    #             )
    #             return

    #         # --- Compute Height Above Ground ---
    #         height_above_ground = np.asarray(las.z) - terrain

    #         # --- Reclassify Vegetation Based on Normalized Height ---
    #         original_veg_class = 5
    #         low_class = 3
    #         med_class = 4
    #         high_class = 5

    #         veg_mask = las.classification == original_veg_class
    #         veg_indices = np.where(veg_mask)[0]

    #         if len(veg_indices) == 0:
    #             QMessageBox.information(
    #                 self.iface.mainWindow(),
    #                 "No Vegetation Points",
    #                 "No high vegetation points (class 5) found to reclassify."
    #             )
    #             return

    #         veg_heights = height_above_ground[veg_mask]

    #         low_thresh = 2.0
    #         high_thresh = 10.0

    #         low_mask = veg_heights < low_thresh
    #         med_mask = (veg_heights >= low_thresh) & (veg_heights <= high_thresh)
    #         high_mask = veg_heights > high_thresh

    #         # Update classifications
    #         las.classification[veg_indices[low_mask]] = low_class
    #         las.classification[veg_indices[med_mask]] = med_class
    #         las.classification[veg_indices[high_mask]] = high_class  # Redundant but safe

    #         # --- Save Output File ---
    #         output_path, _ = QFileDialog.getSaveFileName(
    #             self.iface.mainWindow(),
    #             'Save Terrain-Normalized Vegetation File',
    #             os.path.splitext(filename)[0] + '_veg_normalized.laz',
    #             'LiDAR Files (*.las *.laz)'
    #         )
    #         if not output_path:
    #             return

    #         las.write(output_path)

    #         QMessageBox.information(
    #             self.iface.mainWindow(),
    #             "Vegetation Classification Complete",
    #             f"Total high vegetation points processed: {len(veg_indices):,}\n"
    #             f"Low vegetation (< {low_thresh} m): {np.sum(low_mask):,}\n"
    #             f"Medium vegetation ({low_thresh}-{high_thresh} m): {np.sum(med_mask):,}\n"
    #             f"High vegetation (> {high_thresh} m): {np.sum(high_mask):,}\n\n"
    #             f"Output saved to:\n{output_path}"
    #         )

    #     except Exception as e:
    #         QMessageBox.critical(
    #             self.iface.mainWindow(),
    #             "Error During Classification",
    #             f"An error occurred:\n{e}"
    #         )

    #     finally:
    #         loading_dialog.close()
    #         QApplication.restoreOverrideCursor()

    # --------------------------
    # --- Placeholder method ---
    # --------------------------

    def placeholder(self):
        QMessageBox.information(self.iface.mainWindow(), "Title", f"Coming soon!")
