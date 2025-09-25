# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QDialog
from qgis.core import QgsApplication, QgsTask, Qgis, QgsMessageLog

# --- Dialogs and Data Classes imports ---
from .report_data import ReportData
from .report_dialog import ReportDialog

# --- Utility & Report Generation Functions ---
from ..utils import format_global_encoding, format_point_format, gps_time_to_datetime
from .report_functions import generate_txt_report, generate_markdown_report, generate_pdf_report

# -------------------------
# --- Report Generation ---
# -------------------------
# Description:
# This function generates a report based on the LiDAR file's metadata and statistics,
# allowing the user to choose the report format (text, markdown, or PDF) and which metadata to include.
# -------------------------

# ---------------------------------------------
# --- Background Task for Report Generation ---
# ---------------------------------------------

class ReportGenerationTask(QgsTask):
    """Background task for generating LiDAR information reports"""

    def __init__(self, description, filename, report_path, report_format, selected_fields, parent):
        super().__init__(description, QgsTask.CanCancel)
        self.filename = filename
        self.report_path = report_path
        self.report_format = report_format  # "txt", "md", or "pdf"
        self.selected_fields = selected_fields
        self.parent = parent
        self.exception = None

    def run(self):
        try:
            las = laspy.read(self.filename, laz_backend=LazBackend.Lazrs)

            # Extract stats
            unique_classes, class_counts = np.unique(las.classification, return_counts=True)
            unique_returns, ret_counts = np.unique(las.return_number, return_counts=True)

            if hasattr(las, "gps_time"):
                dt_min = gps_time_to_datetime(las.gps_time.min()).isoformat()
                dt_max = gps_time_to_datetime(las.gps_time.max()).isoformat()
            else:
                dt_min = dt_max = None

            # Build ReportData object from user-selected fields
            data = ReportData(
                file_name=os.path.basename(self.filename) if self.selected_fields["file_name"] else None,
                file_source=las.header.file_source_id if self.selected_fields["file_source"] else None,
                global_encoding=format_global_encoding(las.header.global_encoding) if self.selected_fields["global_encoding"] else None,
                system_id=las.header.system_identifier if self.selected_fields["system_id"] else None,
                gen_software=las.header.generating_software if self.selected_fields["gen_software"] else None,
                version=las.header.version if self.selected_fields["version"] else None,
                point_format=format_point_format(las.header.point_format) if self.selected_fields["point_format"] else None,
                creation_date=str(las.header.creation_date) if self.selected_fields["creation_date"] else None,

                min_intensity=las.intensity.min() if self.selected_fields["min_intensity"] else None,
                max_intensity=las.intensity.max() if self.selected_fields["max_intensity"] else None,

                num_points=las.header.point_count if self.selected_fields["num_points"] else None,
                area=(las.header.x_max - las.header.x_min) * (las.header.y_max - las.header.y_min) if self.selected_fields["area"] else None,
                density=(las.header.point_count / ((las.header.x_max - las.header.x_min) * (las.header.y_max - las.header.y_min)))
                        if self.selected_fields["density"] else None,
                bounds=(las.header.mins, las.header.maxs) if self.selected_fields["bounds"] else None,
                x_axis_bounds=(las.header.x_min, las.header.x_max) if self.selected_fields["x_axis_bounds"] else None,
                y_axis_bounds=(las.header.y_min, las.header.y_max) if self.selected_fields["y_axis_bounds"] else None,
                z_axis_bounds=(las.header.z_min, las.header.z_max) if self.selected_fields["z_axis_bounds"] else None,

                min_time=dt_min if self.selected_fields["min_time"] else None,
                max_time=dt_max if self.selected_fields["max_time"] else None,

                unique_classes=unique_classes if self.selected_fields["class_counts"] else None,
                class_counts=class_counts if self.selected_fields["class_counts"] else None,
                unique_returns=unique_returns if self.selected_fields["return_counts"] else None,
                return_counts=ret_counts if self.selected_fields["return_counts"] else None,
            )

            # Generate report in chosen format
            if self.report_format == "pdf":
                generate_pdf_report(self.parent, self.report_path, data)
            elif self.report_format == "md":
                generate_markdown_report(self.parent, self.report_path, data)
            else:
                generate_txt_report(self.parent, self.report_path, data)

            return True
        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        if result:
            QMessageBox.information(
                self.parent.iface.mainWindow(),
                "Success",
                f"Report created at:\n{self.report_path}"
            )
        else:
            msg = f"An error occurred:\n{self.exception}" if self.exception else "Report generation failed."
            QgsMessageLog.logMessage(msg, "MyPlugin", Qgis.Critical)
            QMessageBox.critical(self.parent.iface.mainWindow(), "Error", msg)

        if self in self.parent.running_tasks:
            self.parent.running_tasks.remove(self)

# -------------------------------------
# --- Main Report Generation Method ---
# -------------------------------------

def generate_report(self):
    # Step 1: Select input file path
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        "Select LiDAR File",
        "",
        "LiDAR Files (*.las *.laz)"
    )
    if not filename:
        return

    # Step 2: Ask user what fields to include
    dialog = ReportDialog(self.iface.mainWindow())
    if dialog.exec_() != QDialog.Accepted:
        return

    # Step 3: Choose output format
    if dialog.radioPdf.isChecked():
        ext, fmt, filter_str = ".pdf", "pdf", "PDF Files (*.pdf)"
    elif dialog.radioMarkdown.isChecked():
        ext, fmt, filter_str = ".md", "md", "Markdown Files (*.md)"
    else:
        ext, fmt, filter_str = ".txt", "txt", "Text Files (*.txt)"

    # Step 4: Select output file path
    report_path, _ = QFileDialog.getSaveFileName(
        self.iface.mainWindow(),
        "Save Report",
        os.path.splitext(filename)[0] + "_report" + ext,
        filter_str
    )
    if not report_path:
        return

    # Collect field selections from dialog
    selected_fields = {
        "file_name": dialog.checkFileName.isChecked(),
        "file_source": dialog.checkFileSource.isChecked(),
        "global_encoding": dialog.checkGlobalEncoding.isChecked(),
        "system_id": dialog.checkSystemId.isChecked(),
        "gen_software": dialog.checkGenSoftware.isChecked(),
        "version": dialog.checkVersion.isChecked(),
        "point_format": dialog.checkPointFormat.isChecked(),
        "creation_date": dialog.checkCreationDate.isChecked(),
        "min_intensity": dialog.checkMinIntensity.isChecked(),
        "max_intensity": dialog.checkMaxIntensity.isChecked(),
        "num_points": dialog.checkNumPoints.isChecked(),
        "area": dialog.checkArea.isChecked(),
        "density": dialog.checkDensity.isChecked(),
        "bounds": dialog.checkBounds.isChecked(),
        "x_axis_bounds": dialog.checkXAxisBounds.isChecked(),
        "y_axis_bounds": dialog.checkYAxisBounds.isChecked(),
        "z_axis_bounds": dialog.checkZAxisBounds.isChecked(),
        "min_time": dialog.checkMinTime.isChecked(),
        "max_time": dialog.checkMaxTime.isChecked(),
        "class_counts": dialog.checkClassCounts.isChecked(),
        "return_counts": dialog.checkReturnCounts.isChecked(),
    }

    # Step 5: Create and run the background task
    task_desc = f"Generating report for {os.path.basename(filename)}"
    task = ReportGenerationTask(task_desc, filename, report_path, fmt, selected_fields, self)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        "Task Started",
        "Report generation is running in the background.",
        level=Qgis.Info,
        duration=-1
    )
