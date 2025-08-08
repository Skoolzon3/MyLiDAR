from datetime import datetime, timedelta, timezone
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from io import BytesIO
from matplotlib import pyplot as plt
import numpy as np

# --- Formatting functions for LiDAR data processing ---

def gps_time_to_datetime(gps_time: float) -> datetime:
    gps_epoch = datetime(1980, 1, 6, tzinfo=timezone.utc)
    return gps_epoch + timedelta(seconds=gps_time)

def format_global_encoding(ge):
    return (
        f"  - GPS Time Type: {ge.gps_time_type}\n"
        f"  - Waveform Internal: {ge.waveform_data_packets_internal}\n"
        f"  - Waveform External: {ge.waveform_data_packets_external}\n"
        f"  - Synthetic Returns: {ge.synthetic_return_numbers}\n"
        f"  - WKT: {ge.wkt}\n"
    )

def format_point_format(pf):
    return (
        f"  - Point Format ID: {pf.id}\n"
        f"  - Size: {pf.size} bytes\n"
    )

# --- Graph generation functions for LiDAR data ---

def generate_pie_chart_from_counts(classes, counts):
    class_info = {
        0: ("Created, Never Classified", "#A0A0A0"),
        1: ("Unclassified", "#B0B0B0"),
        2: ("Ground", "#8B4513"),
        3: ("Low Vegetation", "#ADFF2F"),
        4: ("Medium Vegetation", "#32CD32"),
        5: ("High Vegetation", "#006400"),
        6: ("Building", "#FF4500"),
        7: ("Low Point (Noise)", "#D3D3D3"),
        8: ("Model Key-point", "#FFD700"),
        9: ("Water", "#1E90FF"),
        10: ("Rail", "#8B0000"),
        11: ("Road Surface", "#A0522D"),
        12: ("Overlap", "#C0C0C0"),
        13: ("Wire Guard", "#00CED1"),
        14: ("Wire Conductor", "#20B2AA"),
        15: ("Transmission Tower", "#000080"),
        16: ("Wire-structure Connector", "#708090"),
        17: ("Bridge Deck", "#A9A9A9"),
        18: ("High Noise", "#800080")
    }

    labels = [class_info.get(c, (f"Class {c}", "#CCCCCC"))[0] for c in classes]
    colors = [class_info.get(c, ("Unknown", "#CCCCCC"))[1] for c in classes]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts, labels=labels, colors=colors, autopct=lambda pct: f'{pct:.1f}%', startangle=140, textprops={'fontsize': 10, 'fontweight': 'bold'})

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_return_bar_chart(unique_returns, return_counts):
    from io import BytesIO
    import matplotlib.pyplot as plt

    labels = [f"Return {r}" for r in unique_returns]

    fig, ax = plt.subplots(figsize=(6, 4))

    bars = ax.bar(labels, return_counts, color='lightgreen')
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f'{height:,}',
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha='center',
            va='bottom',
            fontsize=10,
            fontweight='bold'
        )

    # Increase y-axis limit to add vertical space above tallest bar
    max_height = max(return_counts)
    ax.set_ylim(0, max_height * 1.10)  # Add 15% headroom

    ax.set_xlabel("Return Number", fontname='Arial')
    ax.set_ylabel("Count", fontname='Arial')
    plt.xticks(rotation=45)

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf

# --- Dialog creation for loading LiDAR files ---

def create_loading_dialog(self):
    loading_dialog = QDialog(self.iface.mainWindow())
    loading_dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
    loading_dialog.setModal(True)
    loading_dialog.setWindowTitle("Loading")

    loading_dialog.setStyleSheet("""
        QDialog {
            background-color: #f0f0f0;
            border: 1px solid #444;
        }
        QLabel {
            font-size: 14px;
            color: #333;
        }
    """)

    layout = QVBoxLayout()
    layout.setContentsMargins(20, 20, 20, 20)
    label = QLabel("Loading LiDAR file...\nPlease wait.")
    label.setAlignment(Qt.AlignCenter)
    label.setFont(QFont("Segoe UI", 10))
    layout.addWidget(label)
    loading_dialog.setLayout(layout)
    loading_dialog.setFixedSize(300, 100)
    return loading_dialog
