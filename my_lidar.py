# --- General imports ---
import os

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QMenu

# --- Method-specific imports ---
from .tools_suite.report_generation.report_generation import generate_report
from .tools_suite.outlier_removal.outlier_removal import remove_outliers
from .tools_suite.overlap_removal.overlap_removal import remove_overlap
from .tools_suite.building_count.building_count import count_buildings
from .tools_suite.statistics_generation.statistics_generation import generate_statistics
from .tools_suite.vegetation_classification.vegetation_classification import classify_vegetation
from .tools_suite.dem_generation.dem_generation import generate_bare_earth_dem

# -----------------------------
# --- My LiDAR Plugin Class ---
# -----------------------------
class MyLiDARPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Initialize actions
        self.report_action = None
        self.outliers_action = None
        self.overlap_action = None
        self.count_action = None
        self.vegetation_action = None
        self.statistics_action = None
        self.dem_action = None

    def tr(self, message):
        return QCoreApplication.translate('LiDAR Document Generator', message)

    def initGui(self):
        report_icon_path = os.path.join(self.plugin_dir, 'icons/report.png')
        cleanup_icon_path = os.path.join(self.plugin_dir, 'icons/cleanup.png')
        overlap_icon_path = os.path.join(self.plugin_dir, 'icons/overlap.png')
        building_icon_path = os.path.join(self.plugin_dir, 'icons/building.png')
        vegetation_icon_path = os.path.join(self.plugin_dir, 'icons/vegetation.png')
        statistics_icon_path = os.path.join(self.plugin_dir, 'icons/statistics.png')
        dem_icon_path = os.path.join(self.plugin_dir, 'icons/dem.png')

        self.menu = QMenu(self.tr("MyLiDAR"), self.iface.mainWindow().menuBar())
        self.iface.mainWindow().menuBar().insertMenu(
            self.iface.mainWindow().menuBar().actions()[-1],
            self.menu
        )

        self.report_action = QAction(QIcon(report_icon_path), self.tr('Generate LiDAR File Report'), self.iface.mainWindow())
        self.report_action.triggered.connect(self.report_generation)
        self.iface.addToolBarIcon(self.report_action)
        self.menu.addAction(self.report_action)

        self.outliers_action = QAction(QIcon(cleanup_icon_path), self.tr('Remove outlier points'), self.iface.mainWindow())
        self.outliers_action.triggered.connect(self.outlier_removal)
        self.iface.addToolBarIcon(self.outliers_action)
        self.menu.addAction(self.outliers_action)

        self.overlap_action = QAction(QIcon(overlap_icon_path), self.tr('Remove overlapping'), self.iface.mainWindow())
        self.overlap_action.triggered.connect(self.overlap_removal)
        self.iface.addToolBarIcon(self.overlap_action)
        self.menu.addAction(self.overlap_action)

        self.vegetation_action = QAction(QIcon(vegetation_icon_path), self.tr('Classify vegetation'), self.iface.mainWindow())
        self.vegetation_action.triggered.connect(self.vegetation_classification)
        self.iface.addToolBarIcon(self.vegetation_action)
        self.menu.addAction(self.vegetation_action)

        # Toolbar-only actions
        self.count_action = QAction(QIcon(building_icon_path), self.tr('Count buildings'), self.iface.mainWindow())
        self.count_action.triggered.connect(self.building_count)
        self.menu.addAction(self.count_action)

        self.statistics_action = QAction(QIcon(statistics_icon_path), self.tr('View file statistics'), self.iface.mainWindow())
        self.statistics_action.triggered.connect(self.statistics_generation)
        self.menu.addAction(self.statistics_action)

        self.dem_action = QAction(QIcon(dem_icon_path), self.tr('Generate Bare Earth DEM'), self.iface.mainWindow())
        self.dem_action.triggered.connect(self.bare_earth_dem_generation)
        self.menu.addAction(self.dem_action)

    def unload(self):
        self.menu.removeAction(self.report_action)
        self.menu.removeAction(self.outliers_action)
        self.menu.removeAction(self.overlap_action)
        self.menu.removeAction(self.count_action)
        self.menu.removeAction(self.vegetation_action)
        self.menu.removeAction(self.statistics_action)
        self.menu.removeAction(self.dem_action)

        self.iface.removeToolBarIcon(self.report_action)
        self.iface.removeToolBarIcon(self.outliers_action)
        self.iface.removeToolBarIcon(self.overlap_action)
        self.iface.removeToolBarIcon(self.count_action)
        self.iface.removeToolBarIcon(self.vegetation_action)
        self.iface.removeToolBarIcon(self.statistics_action)
        # self.iface.removeToolBarIcon(self.dem_action)

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

    # --- Bare Earth DEM Generation ---
    def bare_earth_dem_generation(self):
        generate_bare_earth_dem(self)

    # --- Placeholder method ---
    def placeholder(self):
        QMessageBox.information(self.iface.mainWindow(), "Title", f"Coming soon!")
