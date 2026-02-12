# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from qgis.core import QgsApplication, QgsPointCloudLayer, QgsProject, QgsTask, Qgis, QgsMessageLog, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QDateTime

# --- Method-specific imports ---
from scipy.spatial import cKDTree

# --- Dialog imports ---
from .outlier_removal_dialog import OutlierRemovalDialog

# -----------------------
# --- Outlier Removal ---
# --------------------------------------------------------------------------------------------
# Description:
# This function removes outliers from a LiDAR file based on a specified radius and minimum
# number of neighbors. It uses a KD-tree during neighbor searching and allows the user to save
# the processed file.
# --------------------------------------------------------------------------------------------

# -------------------------------------------
# --- Background Task for Outlier Removal ---
# -------------------------------------------

class RemoveOutliersTask(QgsTask):
    """Remove outlier points from a LiDAR file in a background thread"""

    def __init__(self, description, input_filename, output_filename, radius, min_neighbors, parent, translator, log_filename=None):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.radius = radius
        self.min_neighbors = min_neighbors
        self.parent = parent
        self.exception = None
        self.tr = translator
        self.num_removed = 0
        self.num_remaining = 0
        self.output_crs = None
        self.log_filename = log_filename
        self.log_entries = []

    def log_step(self, step_name, details="", relevancy="info"):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        levels = {
            "info": (Qgis.Info, "INFO"),
            "warning": (Qgis.Warning, "WARNING"),
            "critical": (Qgis.Critical, "CRITICAL")
        }
        level = levels.get(relevancy, levels["info"])
        entry = f"[{timestamp}] {level[1]}  {step_name}: {details}"
        self.log_entries.append(entry)
        QgsMessageLog.logMessage(f"{step_name}: {details}", "MyLiDAR", level[0])

    def run(self):
        try:
            self.log_step("PROCESS START", f"Input: {os.path.basename(self.input_filename)}, Radius: {self.radius}, Min neighbors: {self.min_neighbors}", "info")

            # Step 1: Read input file
            self.log_step("READING INPUT FILE", self.input_filename, "info")
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            pycrs = las.header.parse_crs(prefer_wkt=True)
            if pycrs:
                self.output_crs = QgsCoordinateReferenceSystem(pycrs.to_wkt())
                self.log_step("CRS DETECTED", f"From file header: {self.output_crs.authid()}", "info")
            else:
                self.log_step("CRS WARNING", self.tr("No CRS found in file header. Checking input layer loaded in QGIS"), "warning")

                matched_layer = None
                for lyr in QgsProject.instance().mapLayers().values():
                    if isinstance(lyr, QgsPointCloudLayer) and lyr.source() == self.input_filename:
                        matched_layer = lyr
                        break
                if matched_layer:
                    if matched_layer.crs().isValid():
                        self.output_crs = matched_layer.crs()
                        self.log_step("CRS ASSIGNED", f"{self.tr('Using CRS assigned in QGIS')}: {self.output_crs.authid()}", "info")
                    else:
                        self.log_step("INVALID CRS", self.tr("Matched layer CRS is invalid, no CRS will be assigned"), "warning")

                else:
                    self.log_step("NO LAYER MATCH", self.tr("Input file not found among loaded layers. Cannot import CRS from QGIS"), "warning")

            self.setProgress(10)

            # Step 2: Build KD-tree
            self.log_step("BUILDING KD-TREE", f"Indexing {las.header.point_count:,} points", "info")
            coords = np.vstack((las.x, las.y, las.z)).T
            tree = cKDTree(coords)
            self.setProgress(20)

            # Step 3: Find outliers
            self.log_step("DETECTING OUTLIERS", f"Processing {las.header.point_count:,} points in batches", "info")
            n_points = coords.shape[0]
            batch_size = max(10000, n_points // 100)  # ~100 updates
            neighbor_counts = np.empty(n_points, dtype=np.int32)

            for i in range(0, n_points, batch_size):
                if self.isCanceled():
                    self.log_step("PROCESS CANCELED", f"at batch {i//batch_size + 1}", "warning")
                    return False

                j = min(i + batch_size, n_points)
                neighbor_counts[i:j] = tree.query_ball_point(coords[i:j], r=self.radius, return_length=True)

                progress = 20 + (70 * j / n_points) # Progress updated proportionally (20–90%)
                self.setProgress(progress)

            # Step 4: Build mask
            mask = neighbor_counts >= self.min_neighbors
            self.num_removed = np.sum(~mask)
            self.num_remaining = np.sum(mask)
            self.log_step("OUTLIER STATISTICS", f"Removed: {self.num_removed:,} ({100*self.num_removed/n_points:.1f}%), "f"Kept: {self.num_remaining:,} ({100*self.num_remaining/n_points:.1f}%)", "info")

            if self.num_remaining == 0:
                error_msg = "All points were classified as outliers. No data would remain"
                self.log_step("CRITICAL ERROR", self.tr(error_msg), "critical")
                raise ValueError(self.tr(error_msg))

            # Step 5: Create new LasData object with the filtered points
            self.log_step("CREATING FILTERED LAS", f"Copying {self.num_remaining:,} points", "info")
            new_header = las.header.copy()
            las_filtered = laspy.LasData(new_header)
            las_filtered.points = las.points[mask]

            # Recalculate the header extents
            filtered_coords = coords[mask]
            las_filtered.header.min = [np.min(filtered_coords[:, 0]), np.min(filtered_coords[:, 1]), np.min(filtered_coords[:, 2])]
            las_filtered.header.max = [np.max(filtered_coords[:, 0]), np.max(filtered_coords[:, 1]), np.max(filtered_coords[:, 2])]
            self.log_step("HEADER UPDATED", f"New extents: {las_filtered.header.min} to {las_filtered.header.max}", "info")

            # Step 6: Write new file to the output path
            self.log_step("WRITING OUTPUT FILE", self.output_filename, "info")
            las_filtered.write(self.output_filename)
            self.setProgress(100)

            self.log_step("PROCESS COMPLETED SUCCESSFULLY", f"Output saved: {self.output_filename}", "info")
            return True

        except Exception as e:
            self.log_step("PROCESS FAILED", f"Error: {str(e)}", "critical")
            self.exception = e
            return False

    def finished(self, result):
        try:
            if result:
                # Task completed successfully
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Outlier Removal Complete"),
                    f"{self.tr('Removed outlier points')}: {self.num_removed:,}\n"
                    f"{self.tr('Remaining points')}: {self.num_remaining:,}\n\n"
                    f"{self.tr('Filtered file saved to')}:\n{self.output_filename}"
                )

                layer_name = os.path.splitext(os.path.basename(self.output_filename))[0]
                pc_layer = QgsPointCloudLayer(self.output_filename, layer_name, "pdal")
                if pc_layer.isValid():
                    if self.output_crs and self.output_crs.isValid():
                        pc_layer.setCrs(self.output_crs)
                        QgsMessageLog.logMessage(
                            f"{self.tr('Output layer CRS applied')}: {self.output_crs.authid()} - {self.output_crs.description()}",
                            "MyLiDAR",
                            Qgis.Info
                        )
                    else:
                        QgsMessageLog.logMessage(
                            self.tr("No valid CRS available to assign to the output layer"),
                            "MyLiDAR",
                            Qgis.Warning
                        )
                    QgsProject.instance().addMapLayer(pc_layer)
                else:
                    QMessageBox.warning(
                        self.parent.iface.mainWindow(),
                        self.tr("Layer Load Warning"),
                        self.tr("The LiDAR file was saved but could not be loaded into QGIS")
                    )
            else:
                # Task failed / canceled
                if self.exception:
                    QgsMessageLog.logMessage(f"{self.tr('An error occurred during outlier removal')}: {self.exception}", 'MyLiDAR', Qgis.Critical)
                    QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error Removing Outliers"), f"{self.tr('An error occurred')}:\n{self.exception}")
                else:
                    QgsMessageLog.logMessage(self.tr('Outlier removal was canceled by the user'), 'MyLiDAR', Qgis.Info)

            if self.log_filename:
                try:
                    with open(self.log_filename, 'w', encoding='utf-8') as f:
                        f.write(f"MyLiDAR OUTLIER REMOVAL REPORT\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(f"Input file: {self.input_filename}\n")
                        f.write(f"Output file: {self.output_filename}\n")
                        f.write(f"Parameters: radius={self.radius}, min_neighbors={self.min_neighbors}\n")
                        f.write(f"CRS: {self.output_crs.authid() if self.output_crs else 'Not set'}\n")
                        f.write(f"Points processed: {self.num_removed + self.num_remaining:,}\n")
                        f.write(f"Points removed: {self.num_removed:,} ({100*self.num_removed/(self.num_removed + self.num_remaining):.1f}%)\n")
                        f.write(f"Points remaining: {self.num_remaining:,}\n\n")
                        f.write("PROCESSING STEPS:\n")
                        f.write("-" * 30 + "\n")
                        for entry in self.log_entries:
                            f.write(entry + "\n")

                        if not result and self.exception:
                            f.write(f"\nFINAL STATUS: FAILED\nError: {str(self.exception)}\n")
                        else:
                            f.write(f"\nFINAL STATUS: SUCCESS\n")

                    self.log_step("LOG FILE WRITTEN", self.log_filename, "info")

                except Exception as log_error:
                    QgsMessageLog.logMessage(
                        f"Failed to write log file {self.log_filename}: {log_error}",
                        "MyLiDAR", Qgis.Warning
                    )
        finally:
            if self in self.parent.running_tasks:
                self.parent.running_tasks.remove(self)

# -----------------------------------
# --- Main Outlier Removal Method ---
# -----------------------------------

def remove_outliers(self):
    # Step 1: Select input file path and parameters via dialog
    dialog = OutlierRemovalDialog(self.iface.mainWindow(), translator=self.tr)
    if dialog.exec_() != QDialog.Accepted:
        return

    input_filename, output_filename = dialog.get_input_output()
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

    radius, min_neighbors = dialog.get_values()
    log_filename = dialog.get_log_path()

    # Step 2: Create and run the background task
    task_description = f"{self.tr('Removing outliers from')} {os.path.basename(input_filename)}"
    task = RemoveOutliersTask(task_description, input_filename, output_filename, radius, min_neighbors, self, self.tr, log_filename)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Removing outliers in the background"),
        level=Qgis.Info,
        duration=-1
    )
