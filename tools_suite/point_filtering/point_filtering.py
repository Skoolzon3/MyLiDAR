# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from qgis.core import QgsApplication, QgsPointCloudLayer, QgsProject, QgsTask, Qgis, QgsMessageLog

# --- Dialog imports ---
from .point_filtering_dialog import PointFilteringDialog

# -----------------------
# --- Point Filtering ---
# --------------------------------------------------------------------------------------------
# Description:
# This module filters LiDAR points based on their classification codes. The user can select one
# or more classification values and choose whether to keep or remove the selected classes. The
# resulting filtered point cloud is written to a new LAS/LAZ file.
# --------------------------------------------------------------------------------------------

# -------------------------------------------
# --- Background Task for Point Filtering ---
# -------------------------------------------

class FilterPointsTask(QgsTask):
    """Filters points from a LiDAR file based on classification codes"""

    def __init__(self, description, input_filename, output_filename, selected_classes, parent, translator):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.selected_classes = selected_classes
        self.parent = parent
        self.tr = translator
        self.exception = None
        self.num_removed = 0
        self.num_remaining = 0

    def run(self):
        try:
            # Step 1: Read LAS/LAZ
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            classifications = las.classification
            total_points = len(classifications)
            self.setProgress(10)

            mask = ~np.isin(classifications, self.selected_classes)

            self.num_removed = np.sum(~mask)
            self.num_remaining = np.sum(mask)
            if self.num_remaining == 0:
                raise ValueError(self.tr("No points remain after filtering. No data would remain"))

            self.setProgress(60)

            # Step 3: Write filtered LAS
            new_header = las.header.copy()
            las_filtered = laspy.LasData(new_header)
            las_filtered.points = las.points[mask]

            # Update header extents
            las_filtered.update_header()
            las_filtered.write(self.output_filename)
            self.setProgress(100)

            return True

        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        try:
            if result:
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Point Filtering Complete"),
                    f"{self.tr('Filtered points')}: {self.num_removed:,}\n"
                    f"{self.tr('Remaining points')}: {self.num_remaining:,}\n\n"
                    f"{self.tr('Filtered file saved to')}:\n{self.output_filename}"
                )

                layer_name = os.path.splitext(os.path.basename(self.output_filename))[0]
                pc_layer = QgsPointCloudLayer(self.output_filename, layer_name, "pdal")
                if pc_layer.isValid():
                    QgsProject.instance().addMapLayer(pc_layer)
                else:
                    QMessageBox.warning(
                        self.parent.iface.mainWindow(),
                        self.tr("Layer Load Warning"),
                        self.tr("The LiDAR file was saved but could not be loaded into QGIS")
                    )

            else:
                if self.exception:
                    QgsMessageLog.logMessage(f"{self.tr('An error occurred during point filtering')}: {self.exception}", 'MyLiDAR', Qgis.Critical)
                    QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error Filtering Points"), f"{self.tr('An error occurred')}:\n{self.exception}")
                else:
                    QgsMessageLog.logMessage(self.tr('Point filtering was canceled by the user'), 'MyLiDAR', Qgis.Info)

        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# -----------------------------------
# --- Main Point Filtering Method ---
# -----------------------------------

def filter_points(self):
    # Step 1: Select input/output file path and parameters via dialog
    dialog = PointFilteringDialog(self.iface.mainWindow(), translator=self.tr)
    if dialog.exec_() != QDialog.Accepted:
        return

    input_filename, output_filename = dialog.get_input_output()
    selected_classes = dialog.get_filter_settings()

    if not input_filename:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Input Selected"),
            self.tr("Please select a LiDAR layer or file.")
        )
        return

    if not output_filename:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Output Selected"),
            self.tr("Please specify an output file path.")
        )
        return

    if not selected_classes:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Classes Selected"),
            self.tr("Please choose at least one classification code.")
        )
        return

    # Step 2: Create background task
    desc = f"{self.tr('Filtering points from')} {os.path.basename(input_filename)}"
    task = FilterPointsTask(desc, input_filename, output_filename, selected_classes, self, self.tr)
    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Filtering points in the background"),
        level=Qgis.Info,
        duration=-1
    )
