# --- General imports ---
import os
import json

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtCore import QCoreApplication, QLocale
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QMenu

# --- Method-specific imports ---
from .tools_suite.outlier_removal.outlier_removal import remove_outliers
from .tools_suite.point_filtering.point_filtering import filter_points
from .tools_suite.vegetation_classification.vegetation_classification import classify_vegetation
from .tools_suite.building_count.building_count import count_buildings
from .tools_suite.dem_generation.dem_generation import generate_bare_earth_dem
from .tools_suite.report_generation.report_generation import generate_report

# -----------------------------
# --- My LiDAR Plugin Class ---
# -----------------------------
class MyLiDARPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.running_tasks = []

        self.translations = {}
        system_lang = QLocale.system().name()[:2] # Detect system language ("en", "es")
        self.current_lang = system_lang if system_lang else "en"
        self.load_language(self.current_lang)

        self.outliers_action = None
        self.overlap_action = None
        self.vegetation_action = None
        self.count_action = None
        self.dem_action = None
        self.report_action = None
        self.filter_action = None

    def load_language(self, lang_code: str):
        lang_file = os.path.join(self.plugin_dir, "translations", f"{lang_code}.json")
        if os.path.exists(lang_file):
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        else:
            self.translations = {}

    def tr(self, message: str) -> str:
        return self.translations.get(message, QCoreApplication.translate('MyLiDAR', message))

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
            ("cleanup.png", self.tr("Remove Outlier Points"), self.outlier_removal),
            ("overlap.png", self.tr("Filter Points by Classification"), self.point_filtering),
            ("vegetation.png", self.tr("Classify Vegetation"), self.vegetation_classification),
            ("building.png", self.tr("Count Buildings"), self.building_count),
            ("dem.png", self.tr("Generate Bare Earth DEM"), self.bare_earth_dem_generation),
            ("report.png", self.tr("Generate LiDAR File Report"), self.report_generation)
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

    # --- Outlier Removal ---
    def outlier_removal(self):
        remove_outliers(self)

    # --- Point Filtering ---
    def point_filtering(self):
        filter_points(self)

    # --- Builing Count ---
    def building_count(self):
        count_buildings(self)

    # --- Vegetation Classification ---
    def vegetation_classification(self):
        classify_vegetation(self)

    # --- Bare Earth DEM Generation ---
    def bare_earth_dem_generation(self):
        generate_bare_earth_dem(self)

    # --- Report Generation ---
    def report_generation(self):
        generate_report(self)

    # --- Placeholder method ---
    def placeholder(self):
        QMessageBox.information(self.iface.mainWindow(), "Title", f"Coming soon!")
