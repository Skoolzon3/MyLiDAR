# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np
import matplotlib.pyplot as plt

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QDialog
from qgis.core import QgsApplication, QgsTask, Qgis, QgsMessageLog
from qgis.PyQt.QtCore import Qt

# --- Dialogs and Data Classes imports ---
from .report_data import ReportData
from .report_dialog import ReportDialog
from .report_generation_dock import ReportDock

# --- Utility & Report Generation Functions ---
from ..utils import format_global_encoding, format_point_format, gps_time_to_datetime
from .report_functions import generate_txt_report, generate_markdown_report, generate_pdf_report, generate_dock_content

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
    """Background task for generating LiDAR information reports + dock"""

    def __init__(self, description, filename, report_path, report_format, selected_fields, parent, translator, show_dock=False):
        super().__init__(description, QgsTask.CanCancel)
        self.filename = filename
        self.report_path = report_path
        self.report_format = report_format
        self.selected_fields = selected_fields
        self.parent = parent
        self.exception = None
        self.tr = translator
        self.show_dock = show_dock
        self.report_text = None
        self.figures = []  # list of (figure, title)

    def run(self):
        try:
            # Step 1: Read input file
            las = laspy.read(self.filename, laz_backend=LazBackend.Lazrs)
            self.setProgress(25)

            # Step 2: Extract statistics
            unique_classes, class_counts = np.unique(las.classification, return_counts=True)
            unique_returns, ret_counts = np.unique(las.return_number, return_counts=True)

            if hasattr(las, "gps_time"):
                dt_min = gps_time_to_datetime(las.gps_time.min()).isoformat()
                dt_max = gps_time_to_datetime(las.gps_time.max()).isoformat()
            else:
                dt_min = dt_max = None

            self.setProgress(50)

            # Step 3: Build ReportData
            data = ReportData(
                file_name=os.path.basename(self.filename) if self.selected_fields["file_name"] else None,
                file_source=las.header.file_source_id if self.selected_fields["file_source"] else None,
                global_encoding=format_global_encoding(las.header.global_encoding, self.tr) if self.selected_fields["global_encoding"] else None,
                system_id=las.header.system_identifier if self.selected_fields["system_id"] else None,
                gen_software=las.header.generating_software if self.selected_fields["gen_software"] else None,
                version=las.header.version if self.selected_fields["version"] else None,
                point_format=format_point_format(las.header.point_format, self.tr) if self.selected_fields["point_format"] else None,
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
                x=las.x, y=las.y
            )
            self.setProgress(75)

            # Step 4: Generate dock if requested
            if self.show_dock:
                self.setProgress(60)
                self.report_text = generate_dock_content(self, data, self.tr)

                # --- Classification Pie ---
                classifications = las.classification
                unique_classes, class_counts = np.unique(classifications, return_counts=True)

                classification_info = {
                    0: (self.tr("Created, Never Classified"), "#A0A0A0"), 1: (self.tr("Unclassified"), "#B0B0B0"),
                    2: (self.tr("Ground"), "#8B4513"), 3: (self.tr("Low Vegetation"), "#ADFF2F"),
                    4: (self.tr("Medium Vegetation"), "#32CD32"), 5: (self.tr("High Vegetation"), "#006400"),
                    6: (self.tr("Building"), "#FF4500"), 7: (self.tr("Low Point (Noise)"), "#D3D3D3"),
                    8: (self.tr("Model Key-point"), "#FFD700"), 9: (self.tr("Water"), "#1E90FF"),
                    10: (self.tr("Rail"), "#8B0000"), 11: (self.tr("Road Surface"), "#A0522D"),
                    12: (self.tr("Overlap"), "#C0C0C0"), 13: (self.tr("Wire Guard"), "#00CED1"),
                    14: (self.tr("Wire Conductor"), "#20B2AA"), 15: (self.tr("Transmission Tower"), "#000080"),
                    16: (self.tr("Wire-structure Connector"), "#708090"), 17: (self.tr("Bridge Deck"), "#A9A9A9"),
                    18: (self.tr("High Noise"), "#800080"),
                }

                labels = [classification_info.get(c, (f"{self.tr('Class')} {c}", "#CCCCCC"))[0] for c in unique_classes]
                colors = [classification_info.get(c, ("Unknown", "#CCCCCC"))[1] for c in unique_classes]

                fig1, ax1 = plt.subplots(figsize=(8, 6))
                ax1.pie(class_counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
                ax1.set_title(self.tr("Classification Distribution"), fontweight="bold")
                self.figures.append((fig1, self.tr("Classification Distribution")))
                self.setProgress(70)

                # --- Return Number Histogram ---
                unique_returns, return_counts = np.unique(las.return_number, return_counts=True)
                return_labels = [str(r) for r in unique_returns]

                fig2, ax2 = plt.subplots(figsize=(5, 4))
                bars = ax2.bar(return_labels, return_counts, color="lightgreen")
                for bar, count in zip(bars, return_counts):
                    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                            f"{count}", ha="center", va="bottom", fontsize=10)
                ax2.set_title(self.tr("Return Number Distribution"), fontweight="bold")
                ax2.set_xlabel(self.tr("Return Number"))
                ax2.set_ylabel(self.tr("Count"))
                self.figures.append((fig2, self.tr("Return Number Distribution")))
                self.setProgress(85)

                # --- Density Heatmap ---
                x, y = las.x, las.y
                fig3, ax3 = plt.subplots(figsize=(7, 5))
                h = ax3.hist2d(x, y, bins=500, cmap="viridis")
                fig3.colorbar(h[3], ax=ax3, label="Point Count")
                ax3.set_title(self.tr("Point Density Heatmap"), fontweight="bold")
                ax3.set_xlabel("X")
                ax3.set_ylabel("Y")
                self.figures.append((fig3, self.tr("Point Density Distribution")))

            # Step 5: Save report (only if format & path provided)
            if self.report_format and self.report_path:
                if self.report_format == "pdf":
                    generate_pdf_report(self.parent, self.report_path, data, self.tr)
                elif self.report_format == "md":
                    generate_markdown_report(self.parent, self.report_path, data, self.tr)
                elif self.report_format == "txt":
                    generate_txt_report(self.parent, self.report_path, data, self.tr)

            self.setProgress(100)
            return True

        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        if result:
            if self.show_dock:
                # Create dock if not visible
                if not hasattr(self.parent, "lidar_report_dock") or self.parent.lidar_report_dock is None or not self.parent.lidar_report_dock.isVisible():
                    self.parent.lidar_report_dock = ReportDock(self.parent.iface.mainWindow(), translator=self.tr)
                    self.parent.iface.addDockWidget(Qt.RightDockWidgetArea, self.parent.lidar_report_dock)

                self.parent.lidar_report_dock.clear()
                self.parent.lidar_report_dock.add_text(self.report_text)
                for fig, title in self.figures:
                    self.parent.lidar_report_dock.add_button_for_figure(fig, title=title)

            # Show appropriate success message
            if self.report_path and self.report_format:
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Success"),
                    f"{self.tr('Report created at')}:\n{self.report_path}"
                )
            elif self.show_dock:
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Success"),
                    self.tr("Dock successfully generated in QGIS.")
                )

        else:
            msg = f"{self.tr('An error occurred')}: {self.exception}" if self.exception else self.tr("Report generation failed")
            QgsMessageLog.logMessage(msg, "MyLiDAR", Qgis.Critical)
            QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error"), msg)

        if self in self.parent.running_tasks:
            self.parent.running_tasks.remove(self)

# -------------------------------------
# --- Main Report Generation Method ---
# -------------------------------------

def generate_report(self):
    # Step 1: Select input file path
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        self.tr("Select LiDAR File"),
        "",
        self.tr("LiDAR Files (*.las *.laz)")
    )
    if not filename:
        return

    # Step 2: Ask user what fields to include
    dialog = ReportDialog(self.iface.mainWindow(), translator=self.tr)
    if dialog.exec_() != QDialog.Accepted:
        return

    # Step 3: Retrieve all selected formats (list like ['txt', 'md', 'pdf'])
    selected_formats = dialog.selected_formats()
    generate_dock = dialog.generate_dock()
    if not selected_formats and not generate_dock:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Output Selected"),
            self.tr("Please select at least one output format or enable dock generation.")
        )
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

    # Step 4: Handle dock-only mode
    if generate_dock and not selected_formats:
        task_desc = f"{self.tr('Generating QGIS Dock for')} {os.path.basename(filename)}"
        task = ReportGenerationTask(
            task_desc,
            filename,
            report_path=None,
            report_format=None,
            selected_fields=selected_fields,
            parent=self,
            translator=self.tr,
            show_dock=True
        )

        self.running_tasks.append(task)
        QgsApplication.taskManager().addTask(task)

        self.iface.messageBar().pushMessage(
            self.tr("Task Started"),
            self.tr("Generating QGIS Dock in the background"),
            level=Qgis.Info,
            duration=-1
        )
        return

    # Step 5: For file reports (TXT/MD/PDF)
    default_name = os.path.splitext(filename)[0] + "_report"
    report_base, _ = QFileDialog.getSaveFileName(
        self.iface.mainWindow(),
        self.tr("Save Report As"),
        default_name,
        self.tr("All Files (*)")
    )
    if not report_base:
        return

    format_extensions = {"txt": ".txt", "md": ".md", "pdf": ".pdf"}

    for fmt in selected_formats:
        ext = format_extensions.get(fmt, ".txt")
        report_path = f"{os.path.splitext(report_base)[0]}_{fmt}{ext}"

        task_desc = f"{self.tr("Generating report for")} {os.path.basename(filename)} ({fmt.upper()})"
        task = ReportGenerationTask(
            task_desc,
            filename,
            report_path,
            fmt,
            selected_fields,
            self,
            self.tr,
            show_dock=generate_dock
        )

        self.running_tasks.append(task)
        QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr(f"Report generation is running in the background"),
        level=Qgis.Info,
        duration=-1
    )
