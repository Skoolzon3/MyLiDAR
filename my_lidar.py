import os

# QGIS and PyQt imports
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QMenu
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

from scipy.spatial import cKDTree

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
from .statistics_generation.statistics_generation import generate_statistics
from .vegetation_classification.vegetation_classification import classify_vegetation

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
        self.sixth_action = None

    def tr(self, message):
        return QCoreApplication.translate('LiDAR Document Generator', message)

    def initGui(self):
        report_icon_path = os.path.join(self.plugin_dir, 'icons/report.png')
        cleanup_icon_path = os.path.join(self.plugin_dir, 'icons/cleanup.png')
        overlap_icon_path = os.path.join(self.plugin_dir, 'icons/overlap.png')
        building_icon_path = os.path.join(self.plugin_dir, 'icons/building.png')
        vegetation_icon_path = os.path.join(self.plugin_dir, 'icons/vegetation.png')
        statistics_icon_path = os.path.join(self.plugin_dir, 'icons/statistics.png')

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
        self.fifth_action.triggered.connect(self.vegetation_classification)
        self.menu.addAction(self.fifth_action)

        self.sixth_action = QAction(QIcon(statistics_icon_path), self.tr('View file statistics'), self.iface.mainWindow())
        self.sixth_action.triggered.connect(self.statistics_generation)
        self.menu.addAction(self.sixth_action)

    def unload(self):
        self.menu.removeAction(self.action)
        self.menu.removeAction(self.secondary_action)
        self.menu.removeAction(self.third_action)
        self.menu.removeAction(self.fourth_action)
        self.menu.removeAction(self.fifth_action)
        self.menu.removeAction(self.sixth_action)

        self.iface.removeToolBarIcon(self.action)
        self.iface.removeToolBarIcon(self.secondary_action)
        self.iface.removeToolBarIcon(self.third_action)
        self.iface.removeToolBarIcon(self.fourth_action)
        self.iface.removeToolBarIcon(self.fifth_action)
        self.iface.removeToolBarIcon(self.sixth_action)

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

    # --- Vegetation Classification ---
    def vegetation_classification(self):
        classify_vegetation(self)

    # --- Statistics Generation ---
    def statistics_generation(self):
        generate_statistics(self)

    # --- Placeholder method ---
    def placeholder(self):
        QMessageBox.information(self.iface.mainWindow(), "Title", f"Coming soon!")
