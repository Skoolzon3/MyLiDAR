# --- General imports ---
import os
import laspy
from laspy import LazBackend
import matplotlib.pyplot as plt
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.core import QgsApplication, QgsTask, Qgis, QgsMessageLog
from PyQt5.QtCore import Qt

# --- Method-specific imports ---
from .statistics_generation_dock import LidarStatsDock

# --- Dialog imports ---
from ..utils import gps_time_to_datetime, format_global_encoding, format_point_format

# -----------------------------
# --- Statistics Generation ---
# -----------------------------
# Description:
# This function generates statistics from a LiDAR file on classification and return number distributions,
# as well as point density. It visualizes these statistics using pie charts and histograms.
# -----------------------------

# -------------------------------------------------
# --- Background Task for Statistics Generation ---
# -------------------------------------------------

class StatisticsGenerationTask(QgsTask):
    """Background task for computing LiDAR statistics and plots"""

    def __init__(self, description, filename, parent):
        super().__init__(description, QgsTask.CanCancel)
        self.filename = filename
        self.parent = parent
        self.exception = None

        # Results for GUI thread
        self.stats_text = None
        self.figures = []  # list of (figure, title)

    def run(self):
        try:
            # Step 1: Read input file
            las = laspy.read(self.filename, laz_backend=LazBackend.Lazrs)
            self.setProgress(20)

            # Step 2: Extract stats
            # --- Metadata ---
            header = las.header
            file_source_id = header.file_source_id
            global_encoding = header.global_encoding
            system_id = header.system_identifier
            generating_software = header.generating_software
            version = f"{header.version.major}.{header.version.minor}"
            point_format = header.point_format
            creation_date = header.creation_date

            # --- Intensity ---
            min_intensity = np.min(las.intensity)
            max_intensity = np.max(las.intensity)

            # --- Spatial ---
            num_points = len(las.points)
            x_min, x_max = np.min(las.x), np.max(las.x)
            y_min, y_max = np.min(las.y), np.max(las.y)
            z_min, z_max = np.min(las.z), np.max(las.z)
            area = (x_max - x_min) * (y_max - y_min)
            density = num_points / area if area > 0 else 0

            bounds = (x_min, x_max, y_min, y_max, z_min, z_max)
            x_axis_bounds, y_axis_bounds, z_axis_bounds = (x_min, x_max), (y_min, y_max), (z_min, z_max)

            # --- GPS Time ---
            if "gps_time" in las.point_format.dimension_names:
                min_time = gps_time_to_datetime(np.min(las.gps_time)).isoformat()
                max_time = gps_time_to_datetime(np.max(las.gps_time)).isoformat()
            else:
                min_time, max_time = None, None

            # --- Stats text ---
            self.stats_text = f"""=============================
--- LiDAR File Statistics ---
=============================

--- Metadata ---
File name: {self.filename}
File source ID: {file_source_id}
Global encoding: \n{format_global_encoding(global_encoding)}
System ID: {system_id}
Generating software: {generating_software}
LAS version: {version}
Point format: \n{format_point_format(point_format)}
Creation date: {creation_date if creation_date else "N/A"}

--- Intensity ---
Min: {min_intensity}
Max: {max_intensity}

--- Spatial Measures ---
Num Points: {num_points:,}
Area: {area:,.2f} m²
Density: {density:.4f} pts/m²
Bounds: {bounds}
  - X-axis: {x_axis_bounds}
  - Y-axis: {y_axis_bounds}
  - Z-axis: {z_axis_bounds}

--- GPS Time ---
Min: {min_time if min_time else "N/A"}
Max: {max_time if max_time else "N/A"}
"""
            self.setProgress(40)

            # Step 3: Generate graphs
            # --- Classification Pie ---
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

            fig1, ax1 = plt.subplots(figsize=(8, 6))
            ax1.pie(class_counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
            ax1.set_title("Classification Distribution", fontweight="bold")
            self.figures.append((fig1, "Classification Distribution"))
            self.setProgress(60)

            # --- Return Number Histogram ---
            unique_returns, return_counts = np.unique(las.return_number, return_counts=True)
            return_labels = [str(r) for r in unique_returns]

            fig2, ax2 = plt.subplots(figsize=(5, 4))
            bars = ax2.bar(return_labels, return_counts, color="lightgreen")
            for bar, count in zip(bars, return_counts):
                ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f"{count}", ha="center", va="bottom", fontsize=9, fontweight="bold")
            ax2.set_title("Return Number Distribution", fontweight="bold")
            ax2.set_xlabel("Return Number")
            ax2.set_ylabel("Count")
            self.figures.append((fig2, "Return Number Distribution"))
            self.setProgress(80)

            # --- Density Heatmap ---
            x, y = las.x, las.y
            fig3, ax3 = plt.subplots(figsize=(7, 5))
            h = ax3.hist2d(x, y, bins=500, cmap="viridis")
            fig3.colorbar(h[3], ax=ax3, label="Point Count")
            ax3.set_title("Point Density Heatmap", fontweight="bold")
            ax3.set_xlabel("X")
            ax3.set_ylabel("Y")
            self.figures.append((fig3, "Point Density Distribution"))
            self.setProgress(100)
            return True

        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        if result:
            if not hasattr(self.parent, "lidar_stats_dock") or self.parent.lidar_stats_dock is None or not self.parent.lidar_stats_dock.isVisible():
                self.parent.lidar_stats_dock = LidarStatsDock(self.parent.iface.mainWindow())
                self.parent.iface.addDockWidget(Qt.RightDockWidgetArea, self.parent.lidar_stats_dock)

            self.parent.lidar_stats_dock.clear()
            self.parent.lidar_stats_dock.add_text(self.stats_text)

            for fig, title in self.figures:
                self.parent.lidar_stats_dock.add_button_for_figure(fig, title=title)

            QMessageBox.information(
                self.parent.iface.mainWindow(),
                "Success",
                f"Statistics generated"
            )
        else:
            msg = f"An error occurred: {self.exception}" if self.exception else "Statistics generation failed."
            QgsMessageLog.logMessage(msg, "MyPlugin", Qgis.Critical)
            QMessageBox.critical(self.parent.iface.mainWindow(), "Error Generating Statistics", msg)

        if self in self.parent.running_tasks:
            self.parent.running_tasks.remove(self)

# -------------------------------------
# --- Main Report Generation Method ---
# -------------------------------------

def generate_statistics(self):
    # Step 1: Select input file path
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        "Select LiDAR File to Analyze",
        "",
        "LiDAR Files (*.las *.laz)"
    )
    if not filename:
        return

    # Step 2: Create and run the background task
    task_desc = f"Generating statistics for {os.path.basename(filename)}"
    task = StatisticsGenerationTask(task_desc, filename, self)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        "Task Started",
        "Generating statistics in the background.",
        level=Qgis.Info,
        duration=-1
    )
