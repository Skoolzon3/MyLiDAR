import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox, QDialog
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel, QDialog, QVBoxLayout
from PyQt5.QtCore import Qt

from .report_data import ReportData
from .report_functions import generate_txt_report, generate_markdown_report, generate_pdf_report
from .report_dialog import ReportDialog

# Backend imports
import laspy
from laspy import LazBackend

# Data handling imports
import numpy as np

# Timestamp handling imports
from .utils import gps_time_to_datetime

# ----------------------------------------
# --- Document Generation Plugin Class ---
# ----------------------------------------
class DocumentGenerationPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None

    def tr(self, message):
        return QCoreApplication.translate('LiDAR Document Generator', message)

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icons/start.png')
        self.action = QAction(QIcon(icon_path), self.tr('Generate LiDAR File Report'), self.iface.mainWindow())
        self.action.triggered.connect(self.generate_report)

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.tr('&LiDAR Report'), self.action)

    def unload(self):
        self.iface.removePluginMenu(self.tr('&LiDAR Report'), self.action)
        self.iface.removeToolBarIcon(self.action)

# --- Main Report Generation Function ---

    def generate_report(self):
        filename, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            'Select LiDAR File',
            '',
            'LiDAR Files (*.las *.laz)'
        )
        if not filename:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        loading_dialog = QDialog(self.iface.mainWindow())
        loading_dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        loading_dialog.setModal(True)
        loading_dialog.setWindowTitle("Loading")
        layout = QVBoxLayout()
        label = QLabel("Loading and analyzing LiDAR file...\nPlease wait.")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        loading_dialog.setLayout(layout)
        loading_dialog.setFixedSize(300, 100)

        try:
            try:
                loading_dialog.show()
                QApplication.processEvents()

                las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

                num_points = las.header.point_count                 # Total number of points in the file
                point_format = las.header.point_format              # Point format
                version = las.header.version                        # LAS version (e.g., 1.4)

                bounds = las.header.mins, las.header.maxs           # Bounds of the point cloud
                x_axis_bounds = las.header.x_max, las.header.x_min  # Bounds for X-axis
                y_axis_bounds = las.header.y_max, las.header.y_min  # Bounds for Y-axis

                # TODO: implement the following attributes
                unique_classes, class_counts = np.unique(las.classification, return_counts=True)  # Classification values and their counts
                unique_returns, ret_counts = np.unique(las.return_number, return_counts=True)   # Return number values and their counts

                if hasattr(las, "gps_time"):    # Check if GPS time is present. This should, in theory, always be true for LAS files.
                        dt_min = gps_time_to_datetime(las.gps_time.min()).isoformat()
                        dt_max = gps_time_to_datetime(las.gps_time.max()).isoformat()
                else:
                    dt_min = dt_max = None
                    QMessageBox.warning(self.iface.mainWindow(), "Warning", "GPS Time not found in the file. This should NOT HAPPEN")

            finally:
                loading_dialog.close()
                QApplication.restoreOverrideCursor()

            QMessageBox.information(self.iface.mainWindow(), "File Info",
                f"File Name: {os.path.basename(filename)}\n"
                f"Min Intensity: {las.intensity.min() if hasattr(las, 'intensity') else 'N/A'}\n"
                f"Max Intensity: {las.intensity.max() if hasattr(las, 'intensity') else 'N/A'}\n"
                f"Unique Classes: {unique_classes}\n"
                f"Unique Returns: {unique_returns}"
            )

            dialog = ReportDialog(self.iface.mainWindow())
            if dialog.exec_() != QDialog.Accepted:
                return

            # is_txt = dialog.radioTxt.isChecked()
            is_md = dialog.radioMarkdown.isChecked()
            is_pdf = dialog.radioPdf.isChecked()

            if is_pdf:
                ext = ".pdf"
                filter_str = "PDF Files (*.pdf)"
            elif is_md:
                ext = ".md"
                filter_str = "Markdown Files (*.md)"
            else:
                ext = ".txt"
                filter_str = "Text Files (*.txt)"

            report_path, _ = QFileDialog.getSaveFileName(
                self.iface.mainWindow(),
                'Save Report',
                os.path.splitext(filename)[0] + '_report' + ext,
                filter_str
            )
            if not report_path:
                return

            data = ReportData(
                file_name=os.path.basename(filename) if dialog.checkFileName.isChecked() else None,
                version=version if dialog.checkVersion.isChecked() else None,
                point_format=point_format if dialog.checkPointFormat.isChecked() else None,
                num_points=num_points if dialog.checkNumPoints.isChecked() else None,
                bounds=bounds if dialog.checkBounds.isChecked() else None,
                x_axis_bounds=x_axis_bounds if dialog.checkXAxisBounds.isChecked() else None,
                y_axis_bounds=y_axis_bounds if dialog.checkYAxisBounds.isChecked() else None,
                file_source=las.header.file_source_id if dialog.checkFileSource.isChecked() else None,
                global_encoding=las.header.global_encoding if dialog.checkGlobalEncoding.isChecked() else None,
                system_id=las.header.system_identifier if dialog.checkSystemId.isChecked() else None,
                gen_software=las.header.generating_software if dialog.checkGenSoftware.isChecked() else None,
                creation_date=str(las.header.creation_date) if dialog.checkCreationDate.isChecked() else None,

                unique_classes=unique_classes if dialog.checkClassCounts.isChecked() else None,
                class_counts=class_counts if dialog.checkClassCounts.isChecked() else None,
                unique_returns=unique_returns if dialog.checkReturnCounts.isChecked() else None,
                return_counts=ret_counts if dialog.checkReturnCounts.isChecked() else None,

                min_intensity=las.intensity.min() if dialog.checkMinIntensity.isChecked() else None,
                max_intensity=las.intensity.max() if dialog.checkMaxIntensity.isChecked() else None,

                min_time=dt_min if dialog.checkMinTime.isChecked() else None,
                max_time=dt_max if dialog.checkMaxTime.isChecked() else None,

                area=(las.header.x_max - las.header.x_min) * (las.header.y_max - las.header.y_min) if dialog.checkArea.isChecked() else None,
                density=las.header.point_count / (
                    (las.header.x_max - las.header.x_min) * (las.header.y_max - las.header.y_min)
                ) if dialog.checkDensity.isChecked() else None,
            )

            if is_pdf:
                generate_pdf_report(self, report_path, data)
            elif is_md:
                generate_markdown_report(self, report_path, data)
            else:
                generate_txt_report(self, report_path, data)

            QMessageBox.information(self.iface.mainWindow(), "Success", f"Report created at {report_path}")

        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Error", f"Failed to process file:\n{e}")

        finally:
            loading_dialog.close()
            QApplication.restoreOverrideCursor()
