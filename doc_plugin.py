import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.PyQt.QtGui import QIcon

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog

from reportlab.pdfgen.canvas import Canvas

import laspy
from laspy import LazBackend

# Load the .ui file dynamically
FormClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "./plugin_ui/report_form.ui"))

class ReportDialog(QDialog, FormClass):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Connect buttons to custom slots
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

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

    def generate_report(self):
        # Select LAS/LAZ file
        filename, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            'Select LiDAR File',
            '',
            'LiDAR Files (*.las *.laz)'
        )
        if not filename:
            return

        try:
            # Case sensitive, watch out!
            # Backends: LazrsParallel, Lazrs, Laszip
            las = laspy.read(filename, laz_backend=LazBackend.Lazrs)
            num_points = las.header.point_count         # Number of points in the file
            bounds = las.header.mins, las.header.maxs   # Bounds of the point cloud
            point_format = las.header.point_format      # Point format of the file
            version = las.header.version                # Version of the LAS file
            x_axis_bounds = las.header.x_max, las.header.x_min # X-axis bounds
            y_axis_bounds = las.header.y_max, las.header.y_min # Y-axis bounds

            QMessageBox.information(self.iface.mainWindow(), "LiDAR File Info",
                                    f"File: {os.path.basename(filename)}\n"
                                    f"Version: {version}\n"
                                    f"Point Format: {point_format}\n"
                                    f"Number of Points: {num_points}\n"
                                    f"Bounds Min: {bounds[0]}\n"
                                    f"Bounds Max: {bounds[1]}\n"
                                    f"X-Axis Bounds: {x_axis_bounds}\n"
                                    f"Y-Axis Bounds: {y_axis_bounds}")

            # Show the dialog to select what to include
            dialog = ReportDialog(self.iface.mainWindow())
            result = dialog.exec_()
            if result != QDialog.Accepted:
                return

            include_file_name = dialog.checkFileName.isChecked()
            include_version = dialog.checkVersion.isChecked()
            include_point_format = dialog.checkPointFormat.isChecked()
            include_num_points = dialog.checkNumPoints.isChecked()
            include_bounds = dialog.checkBounds.isChecked()
            include_x_axis = dialog.checkXAxisBounds.isChecked()
            include_y_axis = dialog.checkYAxisBounds.isChecked()

            report_path, _ = QFileDialog.getSaveFileName(
                self.iface.mainWindow(),
                'Save Report',
                os.path.splitext(filename)[0] + '_report.txt',
                'Text Files (*.txt)'
            )

            if not report_path:
                return

            with open(report_path, "w") as report_file:
                report_file.write("LiDAR File Report\n")
                report_file.write("==================\n")
                if include_file_name:
                    report_file.write(f"File: {os.path.basename(filename)}\n")
                if include_version:
                    report_file.write(f"Version: {version}\n")
                if include_point_format:
                    report_file.write(f"Point Format: {point_format}\n")
                if include_num_points:
                    report_file.write(f"Number of Points: {num_points}\n")
                if include_bounds:
                    report_file.write(f"Bounds Min: {bounds[0]}\n")
                    report_file.write(f"Bounds Max: {bounds[1]}\n")
                if include_x_axis:
                    report_file.write(f"X-Axis Bounds: {x_axis_bounds}\n")
                if include_y_axis:
                    report_file.write(f"Y-Axis Bounds: {y_axis_bounds}\n")

            QMessageBox.information(self.iface.mainWindow(), "Success", f"Report created:\n{report_path}")

        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Error", f"Failed to process file:\n{e}")
