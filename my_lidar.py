# --- General imports ---
import os

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QMenu

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
        self.running_tasks = []

        self.report_action = None
        self.outliers_action = None
        self.overlap_action = None
        self.count_action = None
        self.vegetation_action = None
        self.dem_action = None
        self.statistics_action = None

    def tr(self, message: str) -> str:
        return QCoreApplication.translate('MyLiDAR', message)

    def initGui(self):
        main_win = self.iface.mainWindow()
        self.menu = QMenu("MyLiDAR", main_win)

        menubar = main_win.menuBar()
        help_menu = None
        for act in menubar.actions():
            if act.text().replace("&", "").lower() == "help":
                help_menu = act
                break

        if help_menu:
            menubar.insertMenu(help_menu, self.menu)
        else:
            menubar.addMenu(self.menu)

        actions = [
            ("report.png", self.tr("Generate LiDAR File Report"), self.report_generation),
            ("cleanup.png", self.tr("Remove outlier points"), self.outlier_removal),
            ("overlap.png", self.tr("Remove overlapping"), self.overlap_removal),
            ("vegetation.png", self.tr("Classify vegetation"), self.vegetation_classification),
            ("building.png", self.tr("Count buildings"), self.building_count),
            ("dem.png", self.tr("Generate Bare Earth DEM"), self.bare_earth_dem_generation),
            ("statistics.png", self.tr("View file statistics"), self.statistics_generation),
        ]

        self.actions = []
        for icon_file, label, callback in actions:
            icon_path = os.path.join(self.plugin_dir, 'icons', icon_file)
            action = QAction(QIcon(icon_path), self.tr(label), main_win)
            action.triggered.connect(callback)
            self.menu.addAction(action)
            self.actions.append(action)

    def unload(self):
        if self.menu:
            self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
        self.menu = None
        self.actions = []

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

    # --- Bare Earth DEM Generation ---
    def bare_earth_dem_generation(self):
        generate_bare_earth_dem(self)

    # --- Statistics Generation ---
    def statistics_generation(self):
        generate_statistics(self)

    # --- Placeholder method ---
    def placeholder(self):
        QMessageBox.information(self.iface.mainWindow(), "Title", f"Coming soon!")
