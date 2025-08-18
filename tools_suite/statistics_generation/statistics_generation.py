# --- General imports ---
import laspy
from laspy import LazBackend
import matplotlib.pyplot as plt
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# --- Method-specific imports ---
from .statistics_generation_dock import LidarStatsDock

# --- Dialog imports ---
from ...utils import create_loading_dialog
from ...utils import gps_time_to_datetime, format_global_encoding, format_point_format

# -----------------------------
# --- Statistics Generation ---
# -----------------------------
# Description:
# This function generates statistics from a LiDAR file on classification and return number distributions,
# as well as point density. It visualizes these statistics using pie charts and histograms.
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

    loading_dialog = create_loading_dialog(self, message="Generating statistics...")

    try:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        loading_dialog.show()
        QApplication.processEvents()

        las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

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

        # --- Spatial Measures ---
        num_points = len(las.points)
        x_min, x_max = np.min(las.x), np.max(las.x)
        y_min, y_max = np.min(las.y), np.max(las.y)
        z_min, z_max = np.min(las.z), np.max(las.z)
        area = (x_max - x_min) * (y_max - y_min)
        density = num_points / area if area > 0 else 0

        bounds = (x_min, x_max, y_min, y_max, z_min, z_max)
        x_axis_bounds = (x_min, x_max)
        y_axis_bounds = (y_min, y_max)
        z_axis_bounds = (z_min, z_max)

        # --- GPS Time ---
        if "gps_time" in las.point_format.dimension_names:
            min_time_raw = np.min(las.gps_time)
            max_time_raw = np.max(las.gps_time)
            min_time = gps_time_to_datetime(min_time_raw).isoformat()
            max_time = gps_time_to_datetime(max_time_raw).isoformat()
        else:
            min_time, max_time = None, None

        # --- Stats text ---
        stats_text = f"""=============================
--- LiDAR File Statistics ---
=============================

--- Metadata ---
File name: {filename}
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

        if not hasattr(self, "lidar_stats_dock"):
            self.lidar_stats_dock = LidarStatsDock(self.iface.mainWindow())
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.lidar_stats_dock)

        self.lidar_stats_dock.clear()
        self.lidar_stats_dock.add_text(stats_text)

        # --------------------------
        # --- Classification Pie ---
        # --------------------------
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
        ax1.set_title("Classification Distribution", fontweight='bold')
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        self.lidar_stats_dock.add_button_for_figure(fig1, title="Classification Distribution")

        # -------------------------
        # --- Return Number Bar ---
        # -------------------------
        return_numbers = las.return_number
        unique_returns, return_counts = np.unique(return_numbers, return_counts=True)
        return_labels = [f"{r}" for r in unique_returns]

        fig2, ax2 = plt.subplots(figsize=(5, 4))
        ax2.bar(return_labels, return_counts, color='lightgreen')
        ax2.set_title("Return Number Distribution", fontweight='bold')
        ax2.set_xlabel("Return Number")
        ax2.set_ylabel("Count")
        self.lidar_stats_dock.add_button_for_figure(fig2, title="Return Number Distribution")

        # -----------------------------
        # --- Point Density Heatmap ---
        # -----------------------------
        x, y = las.x, las.y

        fig3, ax3 = plt.subplots(figsize=(7, 5))
        h = ax3.hist2d(x, y, bins=100, cmap='viridis')
        fig3.colorbar(h[3], ax=ax3, label="Point Count")
        ax3.set_title("Point Density Heatmap", fontweight='bold')
        ax3.set_xlabel("X")
        ax3.set_ylabel("Y")
        self.lidar_stats_dock.add_button_for_figure(fig3, title="Point Density Distribution")

    except Exception as e:
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Error Generating Statistics",
            f"An error occurred:\n{e}"
        )

    finally:
        loading_dialog.close()
        QApplication.restoreOverrideCursor()
