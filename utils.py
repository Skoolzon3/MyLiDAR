from datetime import datetime, timedelta, timezone
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

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

# --- Dialog creation for loading LiDAR files ---

def create_loading_dialog(self):
    QApplication.setOverrideCursor(Qt.WaitCursor)
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
