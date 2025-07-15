import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox, QDialogButtonBox
from qgis.PyQt.QtGui import QIcon

import laspy
from laspy import LazBackend

import numpy as np

# User interface imports
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog

# PDF generation imports
from reportlab.pdfgen.canvas import Canvas

# -----------------------
# --- UI Dialog Class ---
# -----------------------
form_class, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "./plugin_ui/report_form.ui"))

class ReportDialog(QDialog, form_class):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.checkboxes = [
            self.checkFileName,
            self.checkVersion,
            self.checkPointFormat,
            self.checkNumPoints,
            self.checkBounds,
            self.checkXAxisBounds,
            self.checkYAxisBounds,
        ]

        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)

        for checkbox in self.checkboxes:
            checkbox.stateChanged.connect(self.update_ok_button)

        self.update_ok_button()

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def update_ok_button(self):
        any_checked = any(cb.isChecked() for cb in self.checkboxes)
        self.ok_button.setEnabled(any_checked)
        # self.labelWarning.setVisible(not any_checked)
        self.labelWarning.setText("" if any_checked else "No information selected.")


# -------------------------
# --- Report Data Class ---
# -------------------------
class ReportData:
    def __init__(self, file_name, version, point_format, num_points,
        bounds, x_axis_bounds, y_axis_bounds, include_file_name,
        include_version, include_point_format, include_num_points,
        include_bounds, include_x_axis, include_y_axis):

        # -- Basic attributes --

        self.file_name = file_name
        self.version = version
        self.point_format = point_format
        self.num_points = num_points
        self.bounds = bounds
        self.x_axis_bounds = x_axis_bounds
        self.y_axis_bounds = y_axis_bounds

        # -- Include flags --

        self.include_file_name = include_file_name
        self.include_version = include_version
        self.include_point_format = include_point_format
        self.include_num_points = include_num_points
        self.include_bounds = include_bounds
        self.include_x_axis = include_x_axis
        self.include_y_axis = include_y_axis

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

# --- Text Report Generation ---

    def generate_txt_report(self, path, data: ReportData):
        with open(path, "w") as f:
            f.write("LiDAR File Report\n")
            f.write("==================\n")
            if data.include_file_name:
                f.write(f"File: {data.file_name}\n")
            if data.include_version:
                f.write(f"Version: {data.version}\n")
            if data.include_point_format:
                f.write(f"Point Format: {data.point_format}\n")
            if data.include_num_points:
                f.write(f"Number of Points: {data.num_points}\n")
            if data.include_bounds:
                f.write(f"Bounds Min: {data.bounds[0]}\n")
                f.write(f"Bounds Max: {data.bounds[1]}\n")
            if data.include_x_axis:
                f.write(f"X-Axis Bounds: {data.x_axis_bounds}\n")
            if data.include_y_axis:
                f.write(f"Y-Axis Bounds: {data.y_axis_bounds}\n")

# --- Markdown Report Generation ---

    def generate_markdown_report(self, path, data: ReportData):
        with open(path, "w") as f:
            f.write("# LiDAR File Report\n\n")
            if data.include_file_name:
                f.write(f"- **File:** `{data.file_name}`\n")
            if data.include_version:
                f.write(f"- **Version:** `{data.version}`\n")
            if data.include_point_format:
                f.write(f"- **Point Format:** `{data.point_format}`\n")
            if data.include_num_points:
                f.write(f"- **Number of Points:** `{data.num_points}`\n")
            if data.include_bounds:
                f.write(f"- **Bounds Min:** `{data.bounds[0]}`\n")
                f.write(f"- **Bounds Max:** `{data.bounds[1]}`\n")
            if data.include_x_axis:
                f.write(f"- **X-Axis Bounds:** `{data.x_axis_bounds}`\n")
            if data.include_y_axis:
                f.write(f"- **Y-Axis Bounds:** `{data.y_axis_bounds}`\n")

# --- PDF Report Generation ---

    def generate_pdf_report(self, path, data: ReportData):
        canvas = Canvas(path)
        canvas.setFont("Helvetica", 12)
        y = 800
        canvas.drawString(50, y, "LiDAR File Report")
        y -= 20
        canvas.drawString(50, y, "==================")
        y -= 30

        def write_line(text):
            nonlocal y
            canvas.drawString(50, y, text)
            y -= 20

        if data.include_file_name:
            write_line(f"File: {data.file_name}")
        if data.include_version:
            write_line(f"Version: {data.version}")
        if data.include_point_format:
            write_line(f"Point Format: {data.point_format}")
        if data.include_num_points:
            write_line(f"Number of Points: {data.num_points}")
        if data.include_bounds:
            write_line(f"Bounds Min: {data.bounds[0]}")
            write_line(f"Bounds Max: {data.bounds[1]}")
        if data.include_x_axis:
            write_line(f"X-Axis Bounds: {data.x_axis_bounds}")
        if data.include_y_axis:
            write_line(f"Y-Axis Bounds: {data.y_axis_bounds}")

        canvas.save()

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

        try:
            las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

            num_points = las.header.point_count                 # Total number of points in the file
            point_format = las.header.point_format              # Point format
            version = las.header.version                        # LAS version (e.g., 1.4)

            bounds = las.header.mins, las.header.maxs           # Bounds of the point cloud
            x_axis_bounds = las.header.x_max, las.header.x_min  # Bounds for X-axis
            y_axis_bounds = las.header.y_max, las.header.y_min  # Bounds for Y-axis

            # TODO: implement the following attributes

            file_source = las.header.file_source_id             # File source ID. If value = 0, no ID assigned
            global_encoding = las.header.global_encoding        # Global encoding bits
            system_id = las.header.system_identifier            # System ID. Value = "LAStools (c) by rapidlasso GmbH" if generated with LASTools
            gen_software = las.header.generating_software       # Generating software
            creation_date = las.header.creation_date            # Creation date in YYYY-MM-DD format

            unique_classes, counts = np.unique(las.classification, return_counts=True)  # Classification values and their counts
            unique_returns, counts = np.unique(las.return_number, return_counts=True)   # Return number values and their counts

            min_intensity = las.intensity.min()         # Minimum intensity value. Note: value lost through conversion with LASTools
            max_intensity = las.intensity.max()         # Maximum intensity value. Note: value lost through conversion with LASTools

            has_gps_time = hasattr(las, "gps_time")
            if has_gps_time:
                min_time = las.gps_time.min()           # Minimum GPS time
                max_time = las.gps_time.max()           # Maximum GPS time

            area = (las.header.x_max - las.header.x_min) * (las.header.y_max - las.header.y_min)    # Area of the point cloud in square units
            density = las.header.point_count / area                                                 # Density of points per square unit

            QMessageBox.information(self.iface.mainWindow(), "File Info",
                f"File Name: {os.path.basename(filename)}\n"
                f"File Source ID: {file_source}\n"
                f"Global Encoding: {global_encoding}\n"
                f"System ID: {system_id}\n"
                f"Generating Software: {gen_software}\n"
                f"Creation Date: {creation_date} (YYYY-MM-DD)\n"
                f"Unique Classes: {len(unique_classes)}\n"
                f"Class Counts: {dict(zip(unique_classes, counts))}\n"
                f"Unique Returns: {len(unique_returns)}\n"
                f"Return Counts: {dict(zip(unique_returns, counts))}\n"
                f"Min GPS Time: {min_time if has_gps_time else 'N/A'}\n"
                f"Max GPS Time: {max_time if has_gps_time else 'N/A'}\n"
                f"Min Intensity: {min_intensity}\n"
                f"Max Intensity: {max_intensity}\n"
                f"Area: {area:.2f} square units\n"
                f"Density: {density:.2f} points per square unit\n"
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
                file_name=os.path.basename(filename),
                version=version,
                point_format=point_format,
                num_points=num_points,
                bounds=bounds,
                x_axis_bounds=x_axis_bounds,
                y_axis_bounds=y_axis_bounds,
                include_file_name=dialog.checkFileName.isChecked(),
                include_version=dialog.checkVersion.isChecked(),
                include_point_format=dialog.checkPointFormat.isChecked(),
                include_num_points=dialog.checkNumPoints.isChecked(),
                include_bounds=dialog.checkBounds.isChecked(),
                include_x_axis=dialog.checkXAxisBounds.isChecked(),
                include_y_axis=dialog.checkYAxisBounds.isChecked()
            )

            if is_pdf:
                self.generate_pdf_report(report_path, data)
            elif is_md:
                self.generate_markdown_report(report_path, data)
            else:
                self.generate_txt_report(report_path, data)

            QMessageBox.information(self.iface.mainWindow(), "Success", f"Report created at {report_path}")

        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Error", f"Failed to process file:\n{e}")
