import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox, QDialogButtonBox
from qgis.PyQt.QtGui import QIcon

# User interface imports
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog

# Backend imports
import laspy
from laspy import LazBackend

# Data handling imports
import numpy as np

# PDF generation imports
from reportlab.pdfgen.canvas import Canvas

# Timestamp handling imports
from datetime import datetime, timedelta, timezone

def gps_time_to_datetime(gps_time: float) -> datetime:
    gps_epoch = datetime(1980, 1, 6, tzinfo=timezone.utc)
    return gps_epoch + timedelta(seconds=gps_time)

# -----------------------
# --- UI Dialog Class ---
# -----------------------
form_class, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "./plugin_ui/report_form.ui"))

class ReportDialog(QDialog, form_class):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.groupTime.toggled.connect(self.on_group_time_toggled)

        self.checkboxes = [
            # Metadata checkboxes
            self.checkFileName,
            self.checkFileSource,
            self.checkGlobalEncoding,
            self.checkSystemId,
            self.checkGenSoftware,
            self.checkVersion,
            self.checkPointFormat,
            self.checkCreationDate,

            # Intensity checkboxes
            self.checkMinIntensity,
            self.checkMaxIntensity,

            # Spatial bounds checkboxes
            self.checkNumPoints,
            self.checkArea,
            self.checkDensity,
            self.checkBounds,
            self.checkXAxisBounds,
            self.checkYAxisBounds,

            # GPS time checkboxes
            self.checkMinTime,
            self.checkMaxTime,
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
        self.labelWarning.setText("" if any_checked else "No information selected.")

    def on_group_time_toggled(self, checked):
        self.checkMinTime.setEnabled(checked)
        self.checkMaxTime.setEnabled(checked)

        if checked:
            self.checkMinTime.setChecked(True)
            self.checkMaxTime.setChecked(True)
        else:
            self.checkMinTime.setChecked(False)
            self.checkMaxTime.setChecked(False)

        self.update_ok_button()

# -------------------------
# --- Report Data Class ---
# -------------------------
class ReportData:
    def __init__(self, file_name, version, point_format,
        num_points, bounds, x_axis_bounds, y_axis_bounds,
        file_source=None, global_encoding=None, system_id=None, gen_software=None,
        creation_date=None, unique_classes=None, class_counts=None, unique_returns=None,
        return_counts=None, min_intensity=None, max_intensity=None, min_time=None,
        max_time=None, area=None, density=None,
    ):
        # -- Metadata --
        self.file_name = file_name
        self.file_source = file_source
        self.global_encoding = global_encoding
        self.system_id = system_id
        self.gen_software = gen_software
        self.version = version
        self.point_format = point_format
        self.creation_date = creation_date

        # -- Classifications and Returns --
        # self.unique_classes = unique_classes              # np.unique(las.classification)
        # self.class_counts = class_counts                  # counts of classifications
        # self.unique_returns = unique_returns              # np.unique(las.return_number)
        # self.return_counts = return_counts                # counts of returns

        # -- Intensity --
        self.min_intensity = min_intensity
        self.max_intensity = max_intensity

        # -- GPS Time --
        self.min_time = min_time
        self.max_time = max_time

        # -- Spatial Measures --
        self.num_points = num_points
        self.area = area
        self.density = density
        self.bounds = bounds
        self.x_axis_bounds = x_axis_bounds
        self.y_axis_bounds = y_axis_bounds

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
        with open(path, "w", encoding="utf-8") as f:
            f.write("==================\n")
            f.write("LiDAR File Report\n")
            f.write("==================\n\n")

            if data.file_name:
                f.write(f"Name: {data.file_name}\n")

            f.write("\n")

            # -- File Metadata --
            if (data.file_source or data.global_encoding or data.system_id or
                data.gen_software or data.version or data.point_format or data.creation_date):
                f.write("File Metadata:\n")
                if data.file_source:
                    f.write(f"File Source ID: {data.file_source}\n")
                if data.global_encoding:
                    f.write(f"Global Encoding: {data.global_encoding}\n")
                if data.system_id:
                    f.write(f"System ID: {data.system_id}\n")
                if data.gen_software:
                    f.write(f"Generating Software: {data.gen_software}\n")
                if data.version:
                    f.write(f"Version: {data.version}\n")
                if data.point_format:
                    f.write(f"Point Format: {data.point_format}\n")
                if data.creation_date:
                    f.write(f"Creation Date: {data.creation_date}\n")

                f.write("\n")

            # -- Intensity --
            if (data.min_intensity or data.max_intensity):
                f.write("Intensity:\n")
                if data.min_intensity:
                    f.write(f"Min Intensity: {data.min_intensity}\n")
                if data.max_intensity:
                    f.write(f"Max Intensity: {data.max_intensity}\n")

                f.write("\n")

            # -- Spatial Measures --
            if (data.num_points or data.area or data.density or
                data.bounds or data.x_axis_bounds or data.y_axis_bounds):
                f.write("Spatial Measures:\n")
                if data.num_points:
                    f.write(f"Number of Points: {data.num_points}\n")
                if data.area:
                    f.write(f"Area: {data.area}\n")
                if data.density:
                    f.write(f"Density: {data.density}\n")
                if data.bounds:
                    f.write(f"Bounds Min: {data.bounds[0]}\n")
                    f.write(f"Bounds Max: {data.bounds[1]}\n")
                if data.x_axis_bounds:
                    f.write(f"X-Axis Bounds: {data.x_axis_bounds}\n")
                if data.y_axis_bounds:
                    f.write(f"Y-Axis Bounds: {data.y_axis_bounds}\n")

                f.write("\n")

            # -- GPS Time --
            if (data.min_time or data.max_time):
                f.write("GPS Time:\n")
                if data.min_time:
                    f.write(f"Min GPS Time: {data.min_time}\n")
                if data.max_time:
                    f.write(f"Max GPS Time: {data.max_time}\n")

            # # -- Classifications --
            # if data.unique_classes is not None and data.class_counts is not None:
            #     f.write("\nClassification Counts:\n")
            #     for cls, count in zip(data.unique_classes, data.class_counts):
            #         f.write(f"  Class {cls}: {count}\n")

            # # -- Returns --
            # if data.unique_returns is not None and data.return_counts is not None:
            #     f.write("\nReturn Number Counts:\n")
            #     for ret, count in zip(data.unique_returns, data.return_counts):
            #         f.write(f"  Return {ret}: {count}\n")

# --- Markdown Report Generation (NEEDS UPDATE) ---

    def generate_markdown_report(self, path, data: ReportData):
        with open(path, "w", encoding="utf-8") as f:
            f.write("# LiDAR File Report\n\n")

            if data.file_name:
                f.write(f"- **File:** `{data.file_name}`\n")

            f.write("\n")

            # -- File Metadata --
            if (data.file_source or data.global_encoding or data.system_id or
                data.gen_software or data.version or data.point_format or data.creation_date):
                f.write("## File Metadata\n")
                if data.file_source:
                    f.write(f"- **File Source ID:** `{data.file_source}`\n")
                if data.global_encoding:
                    f.write(f"- **Global Encoding:** `{data.global_encoding}`\n")
                if data.system_id:
                    f.write(f"- **System ID:** `{data.system_id}`\n")
                if data.gen_software:
                    f.write(f"- **Generating Software:** `{data.gen_software}`\n")
                if data.version:
                    f.write(f"- **Version:** `{data.version}`\n")
                if data.point_format:
                    f.write(f"- **Point Format:** `{data.point_format}`\n")
                if data.creation_date:
                    f.write(f"- **Creation Date:** `{data.creation_date}`\n")

                f.write("\n")

            # -- Intensity --
            if data.min_intensity or data.max_intensity:
                f.write("## Intensity\n")
                if data.min_intensity:
                    f.write(f"- **Min Intensity:** `{data.min_intensity}`\n")
                if data.max_intensity:
                    f.write(f"- **Max Intensity:** `{data.max_intensity}`\n")

                f.write("\n")

            # -- Spatial Measures --
            if (data.num_points or data.area or data.density or
                data.bounds or data.x_axis_bounds or data.y_axis_bounds):
                f.write("## Spatial Measures\n")
                if data.num_points:
                    f.write(f"- **Number of Points:** `{data.num_points}`\n")
                if data.area:
                    f.write(f"- **Area:** `{data.area}`\n")
                if data.density:
                    f.write(f"- **Density:** `{data.density}`\n")
                if data.bounds:
                    f.write(f"- **Bounds Min:** `{data.bounds[0]}`\n")
                    f.write(f"- **Bounds Max:** `{data.bounds[1]}`\n")
                if data.x_axis_bounds:
                    f.write(f"- **X-Axis Bounds:** `{data.x_axis_bounds}`\n")
                if data.y_axis_bounds:
                    f.write(f"- **Y-Axis Bounds:** `{data.y_axis_bounds}`\n")

                f.write("\n")

            # -- GPS Time --
            f.write("## GPS Time\n")
            if (data.min_time or data.max_time):
                f.write("- **GPS Time:** \n")
                if data.min_time:
                    f.write(f"- **Min GPS Time:** `{data.min_time}`\n")
                if data.max_time:
                    f.write(f"- **Max GPS Time:** `{data.max_time}`\n")

# --- PDF Report Generation (NEEDS UPDATE) ---

    def generate_pdf_report(self, path, data: ReportData):
        canvas = Canvas(path)
        canvas.setFont("Helvetica", 12)
        y = 800

        def write_line(text):
            nonlocal y
            canvas.drawString(50, y, text)
            y -= 20
            if y < 50:
                canvas.showPage()
                canvas.setFont("Helvetica", 12)
                y = 800

        # Title
        write_line("LiDAR File Report")
        write_line("==================")
        y -= 10

        # File Name
        if data.file_name:
            write_line(f"File: {data.file_name}")

        y -= 10

        # File Metadata
        if (data.file_source or data.global_encoding or data.system_id or
            data.gen_software or data.version or data.point_format or data.creation_date):
            write_line("File Metadata:")
            if data.file_source:
                write_line(f"  File Source ID: {data.file_source}")
            if data.global_encoding:
                write_line(f"  Global Encoding: {data.global_encoding}")
            if data.system_id:
                write_line(f"  System ID: {data.system_id}")
            if data.gen_software:
                write_line(f"  Generating Software: {data.gen_software}")
            if data.version:
                write_line(f"  Version: {data.version}")
            if data.point_format:
                write_line(f"  Point Format: {data.point_format}")
            if data.creation_date:
                write_line(f"  Creation Date: {data.creation_date}")

            y -= 10

        # Intensity
        if data.min_intensity or data.max_intensity:
            write_line("Intensity:")
            if data.min_intensity:
                write_line(f"  Min Intensity: {data.min_intensity}")
            if data.max_intensity:
                write_line(f"  Max Intensity: {data.max_intensity}")

            y -= 10

        # Spatial Measures
        if (data.num_points or data.area or data.density or
            data.bounds or data.x_axis_bounds or data.y_axis_bounds):
            write_line("Spatial Measures:")
            if data.num_points:
                write_line(f"  Number of Points: {data.num_points}")
            if data.area:
                write_line(f"  Area: {data.area}")
            if data.density:
                write_line(f"  Density: {data.density}")
            if data.bounds:
                write_line(f"  Bounds Min: {data.bounds[0]}")
                write_line(f"  Bounds Max: {data.bounds[1]}")
            if data.x_axis_bounds:
                write_line(f"  X-Axis Bounds: {data.x_axis_bounds}")
            if data.y_axis_bounds:
                write_line(f"  Y-Axis Bounds: {data.y_axis_bounds}")

            y -= 10

        # GPS Time
        write_line("GPS Time:")
        if (data.min_time or data.max_time):
            write_line("  Present: Yes")
            if data.min_time:
                write_line(f"  Min GPS Time: {data.min_time}")
            if data.max_time:
                write_line(f"  Max GPS Time: {data.max_time}")
        else:
            write_line("  Present: No")

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
            unique_classes, class_counts = np.unique(las.classification, return_counts=True)  # Classification values and their counts
            unique_returns, ret_counts = np.unique(las.return_number, return_counts=True)   # Return number values and their counts

            gps_time_present = hasattr(las, "gps_time")  # Check if GPS time is present. This should, in theory, always be true for LAS files.
            if gps_time_present:
                min_time = las.gps_time.min()
                max_time = las.gps_time.max()

                dt_min = gps_time_to_datetime(min_time).isoformat()
                dt_max = gps_time_to_datetime(max_time).isoformat()
            else:
                min_time = max_time = None
                QMessageBox.warning(self.iface.mainWindow(), "Warning", "GPS Time not found in the file. This should NOT HAPPEN")

            # QMessageBox.information(self.iface.mainWindow(), "File Info",
            #     f"File Name: {os.path.basename(filename)}\n"
            #     f"Global Encoding: {las.header.global_encoding}\n"
            #     f"Min Time: {dt_min if gps_time_present else 'N/A'}\n"
            #     f"Max Time: {dt_max if gps_time_present else 'N/A'}\n"
            # )

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

                # unique_classes=unique_classes,
                # class_counts=class_counts,
                # unique_returns=unique_returns,
                # return_counts=ret_counts,

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
                self.generate_pdf_report(report_path, data)
            elif is_md:
                self.generate_markdown_report(report_path, data)
            else:
                self.generate_txt_report(report_path, data)

            QMessageBox.information(self.iface.mainWindow(), "Success", f"Report created at {report_path}")

        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Error", f"Failed to process file:\n{e}")
