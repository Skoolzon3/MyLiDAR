import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox, QDialog
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtCore import Qt

from .report_data import ReportData
from .report_functions import generate_txt_report, generate_markdown_report, generate_pdf_report
from .report_dialog import ReportDialog
from .outlier_removal_dialog import OutlierRemovalDialog

# Backend imports
import laspy
from laspy import LazBackend

# Data handling imports
import numpy as np

# Timestamp handling imports
from .utils import gps_time_to_datetime, create_loading_dialog, format_global_encoding, format_point_format

# Spatial data handling imports
from scipy.spatial import cKDTree

# -----------------------------
# --- My LiDAR Plugin Class ---
# -----------------------------
class MyLiDARPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.secondary_action = None

    def tr(self, message):
        return QCoreApplication.translate('LiDAR Document Generator', message)

    def initGui(self):
        report_icon_path = os.path.join(self.plugin_dir, 'icons/report.png')
        cleanup_icon_path = os.path.join(self.plugin_dir, 'icons/cleanup.png')

        self.action = QAction(QIcon(report_icon_path), self.tr('Generate LiDAR File Report'), self.iface.mainWindow())
        self.action.triggered.connect(self.generate_report)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.tr('&MyLiDAR'), self.action)

        self.secondary_action = QAction(QIcon(cleanup_icon_path), self.tr('Remove outliers'), self.iface.mainWindow())
        self.secondary_action.triggered.connect(self.remove_outliers)
        self.iface.addToolBarIcon(self.secondary_action)
        self.iface.addPluginToMenu(self.tr('&MyLiDAR'), self.secondary_action)

    def unload(self):
        self.iface.removePluginMenu(self.tr('&MyLiDAR'), self.action)
        self.iface.removePluginMenu(self.tr('&MyLiDAR'), self.secondary_action)
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeToolBarIcon(self.secondary_action)

    # -------------------------
    # --- Report Generation ---
    # -------------------------

    def generate_report(self):
        filename, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            'Select LiDAR File',
            '',
            'LiDAR Files (*.las *.laz)'
        )
        if not filename:
            return

        loading_dialog = create_loading_dialog(self)

        try:
            try:
                loading_dialog.show()
                QApplication.processEvents()

                las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

                bounds = las.header.mins, las.header.maxs           # Bounds of the point cloud
                x_axis_bounds = las.header.x_max, las.header.x_min  # Bounds for X-axis
                y_axis_bounds = las.header.y_max, las.header.y_min  # Bounds for Y-axis

                unique_classes, class_counts = np.unique(las.classification, return_counts=True)  # Classification values and their counts
                unique_returns, ret_counts = np.unique(las.return_number, return_counts=True)   # Return number values and their counts

                if hasattr(las, "gps_time"):    # Check if GPS time is present. This should, in theory, always be true for LAS files.
                        dt_min = gps_time_to_datetime(las.gps_time.min()).isoformat()
                        dt_max = gps_time_to_datetime(las.gps_time.max()).isoformat()
                else:
                    dt_min = dt_max = None
                    QMessageBox.warning(self.iface.mainWindow(), "Warning", "GPS Time not found in the file. This may affect the report.")

            finally:
                loading_dialog.close()
                QApplication.restoreOverrideCursor()

            QMessageBox.information(self.iface.mainWindow(), "File Info",
                f"File Name: {os.path.basename(filename)}\n"
                f"File Source ID: {las.header.file_source_id}\n"
                f"System ID: {las.header.system_identifier}"
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
                # -- Metadata --
                file_name=os.path.basename(filename) if dialog.checkFileName.isChecked() else None,             # File name
                file_source=las.header.file_source_id if dialog.checkFileSource.isChecked() else None,          # File source
                global_encoding=format_global_encoding(las.header.global_encoding) if dialog.checkGlobalEncoding.isChecked() else None,     # Global encoding details
                system_id=las.header.system_identifier if dialog.checkSystemId.isChecked() else None,           # Note: System ID only incluided in generated LAZ files
                gen_software=las.header.generating_software if dialog.checkGenSoftware.isChecked() else None,   # Generating software (e.g., LAStools, PDAL)
                version=las.header.version if dialog.checkVersion.isChecked() else None,                        # LAS version (e.g., 1.4)
                point_format=format_point_format(las.header.point_format) if dialog.checkPointFormat.isChecked() else None,                 # Point format details
                creation_date=str(las.header.creation_date) if dialog.checkCreationDate.isChecked() else None,  # Creation date of the file

                # -- Intensity --
                min_intensity=las.intensity.min() if dialog.checkMinIntensity.isChecked() else None,            # Minimum intensity value
                max_intensity=las.intensity.max() if dialog.checkMaxIntensity.isChecked() else None,            # Maximum intensity value

                # -- Spatial --
                num_points=las.header.point_count if dialog.checkNumPoints.isChecked() else None,               # Total number of points in the file
                area=(las.header.x_max - las.header.x_min) * (las.header.y_max - las.header.y_min) if dialog.checkArea.isChecked() else None, # Area covered by the point cloud (width * height)
                density=las.header.point_count / (
                    (las.header.x_max - las.header.x_min) * (las.header.y_max - las.header.y_min)
                ) if dialog.checkDensity.isChecked() else None,                                                 # Density of points (points per square unit)
                bounds=bounds if dialog.checkBounds.isChecked() else None,                                      # Bounds of the point cloud (min, max)
                x_axis_bounds=x_axis_bounds if dialog.checkXAxisBounds.isChecked() else None,                   # Bounds for X-axis
                y_axis_bounds=y_axis_bounds if dialog.checkYAxisBounds.isChecked() else None,                   # Bounds for Y-axis

                # -- GPS Time --
                min_time=dt_min if dialog.checkMinTime.isChecked() else None,                                   # Minimum GPS time
                max_time=dt_max if dialog.checkMaxTime.isChecked() else None,                                   # Maximum GPS time

                # -- Classifications and Returns --
                unique_classes=unique_classes if dialog.checkClassCounts.isChecked() else None,                 # Unique classification values
                class_counts=class_counts if dialog.checkClassCounts.isChecked() else None,
                unique_returns=unique_returns if dialog.checkReturnCounts.isChecked() else None,                # Unique return number values
                return_counts=ret_counts if dialog.checkReturnCounts.isChecked() else None,
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

    def placeholder(self):
        QMessageBox.information(self.iface.mainWindow(), "Title", f"Coming soon!")

    # -----------------------
    # --- Outlier Removal ---
    # -----------------------

    def remove_outliers(self):

        filename, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            'Select LiDAR File to Clean',
            '',
            'LiDAR Files (*.las *.laz)'
        )
        if not filename:
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            'Save Cleaned LiDAR File',
            os.path.splitext(filename)[0] + '_cleaned.laz',
            'LiDAR Files (*.las *.laz)'
        )
        if not output_path:
            return

        dialog = OutlierRemovalDialog(self.iface.mainWindow())
        if dialog.exec_() != QDialog.Accepted:
            return

        radius, min_neighbors = dialog.get_values()

        loading_dialog = create_loading_dialog(self)
        loading_dialog.show()

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QApplication.processEvents()

            las = laspy.read(filename, laz_backend=LazBackend.Lazrs) # Read the LiDAR file (This takes some time)

            coords = np.vstack((las.x, las.y, las.z)).T
            tree = cKDTree(coords)
            neighbor_counts = tree.query_ball_point(coords, r=radius, return_length=True)
            mask = neighbor_counts >= min_neighbors
            num_removed = np.sum(~mask)
            num_remaining = np.sum(mask)

            if num_remaining == 0:
                raise ValueError("All points were classified as outliers — no data would remain.")

            new_header = las.header.copy()
            las_filtered = laspy.LasData(new_header)

            filtered_coords = coords[mask]

            las_filtered.points = las.points[mask]

            las_filtered.header.min = [
                filtered_coords[:, 0].min(),
                filtered_coords[:, 1].min(),
                filtered_coords[:, 2].min()
            ]
            las_filtered.header.max = [
                filtered_coords[:, 0].max(),
                filtered_coords[:, 1].max(),
                filtered_coords[:, 2].max()
            ]

            las_filtered.points = las.points[mask]

            assert len(las_filtered.points) == np.sum(mask)

            las_filtered.write(output_path)

            QMessageBox.information(
                self.iface.mainWindow(),
                "Outlier Removal Complete",
                f"Removed {num_removed:,} outlier points.\n"
                f"Remaining: {num_remaining:,} points\n\n"
                f"Filtered file saved to:\n{output_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Error Removing Outliers",
                f"An error occurred:\n{e}"
            )

        finally:
            loading_dialog.close()
            QApplication.restoreOverrideCursor()
