# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsField, QgsProject, QgsFillSymbol, QgsTask, QgsApplication, Qgis, QgsMessageLog, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsPointCloudLayer
from qgis.PyQt.QtCore import QMetaType

# --- Method-specific imports ---
from sklearn.cluster import DBSCAN
from shapely.geometry import MultiPoint

# --- Dialog imports ---
from .building_count_dialog import BuildingCountDialog

# ----------------------
# --- Building Count ---
# ------------------------------------------------------------------------------------------------
# Description:
# This function counts buildings in LiDAR point clouds through DBSCAN clustering
# on building-classified points, providing an approximate count of buildings based on its results.
# Users can specify parameters for clustering (eps and min_samples).
# ------------------------------------------------------------------------------------------------

# ------------------------------------------
# --- Background Task for Building Count ---
# ------------------------------------------

class BuildingCountTask(QgsTask):
    """Background task for counting buildings using DBSCAN on LiDAR data"""

    def __init__(self, description, input_filename, eps, min_samples, use_z, parent, translator, output_path=None):
        super().__init__(description, QgsTask.CanCancel)
        self.input_filename = input_filename
        self.eps = eps
        self.min_samples = min_samples
        self.use_z = use_z
        self.parent = parent
        self.output_path = output_path

        self.exception = None
        self.tr = translator
        self.num_buildings = 0
        self.num_points = 0
        self.output_crs = None
        self.clusters = []  # list of (cluster_id, coords, area, wkt)

    def run(self):
        try:
            # Step 1: Read input file
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            pycrs = las.header.parse_crs(prefer_wkt=True)
            if pycrs:
                self.output_crs = QgsCoordinateReferenceSystem(pycrs.to_wkt())
            else:
                QgsMessageLog.logMessage(
                    "No CRS found in file header. Checking input layer loaded in QGIS",
                    "MyLiDAR", Qgis.Warning
                )

                matched_layer = None
                for lyr in QgsProject.instance().mapLayers().values():
                    if isinstance(lyr, QgsPointCloudLayer) and lyr.source() == self.input_filename:
                        matched_layer = lyr
                        break

                if matched_layer:
                    if matched_layer.crs().isValid():
                        self.output_crs = matched_layer.crs()
                        QgsMessageLog.logMessage(
                            f"Using CRS assigned in QGIS: {self.output_crs.authid()}",
                            "MyLiDAR", Qgis.Info
                        )
                    else:
                        QgsMessageLog.logMessage(
                            "Matched layer CRS is invalid, no CRS will be assigned",
                            "MyLiDAR", Qgis.Warning
                        )
                else:
                    QgsMessageLog.logMessage(
                        "Input file not found among loaded layers. Cannot import CRS from QGIS",
                        "MyLiDAR", Qgis.Warning
                    )
            self.setProgress(10)

            # Step 2: Filter building-classified points
            building_class_code = 6
            classifications = las.classification
            is_building = classifications == building_class_code

            self.num_points = int(np.sum(is_building))
            if self.num_points == 0:
                self.setProgress(100)
                return True
            self.setProgress(20)

            # Step 3: Extract coordinates for clustering
            if self.use_z:
                coords = np.vstack((las.x[is_building], las.y[is_building], las.z[is_building])).T
            else:
                coords = np.vstack((las.x[is_building], las.y[is_building])).T
            self.setProgress(30)

            # Step 4: DBSCAN clustering
            db = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(coords)
            labels = db.labels_
            self.num_buildings = len(set(labels)) - (1 if -1 in labels else 0)
            self.setProgress(70)

            # Step 5: Convex hulls for clusters
            unique_clusters = [cid for cid in set(labels) if cid != -1]
            total_clusters = len(unique_clusters)

            for idx, cluster_id in enumerate(unique_clusters, start=1):
                if self.isCanceled():
                    return False

                cluster_coords = coords[labels == cluster_id]
                if len(cluster_coords) < self.min_samples:
                    continue
                poly = MultiPoint(cluster_coords).convex_hull
                self.clusters.append((
                    int(cluster_id),
                    len(cluster_coords),
                    poly.area,
                    poly.wkt
                ))

                progress = 80 + (20 * idx / total_clusters)
                self.setProgress(progress)

            self.setProgress(100)
            return True

        except Exception as e:
            self.exception = e
            return False

    def finished(self, result):
        if result:

            if self.num_points == 0:
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("No Buildings Found"),
                    self.tr("No buildings were found in this file")
                )
                return

            else:
                # --- Build QGIS layer ---
                base_name = os.path.splitext(os.path.basename(self.input_filename))[0]
                cluster_suffix = "3D_clustering" if self.use_z else "2D_clustering"
                layer_name = f"{base_name}_{cluster_suffix}"

                vl = QgsVectorLayer("Polygon", layer_name, "memory")
                pr = vl.dataProvider()
                if self.output_crs and self.output_crs.isValid():
                    vl.setCrs(self.output_crs)
                else:
                    vl.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))

                pr.addAttributes([
                    QgsField("cluster_id",  QMetaType.Int,    "integer", 10),
                    QgsField("num_points",  QMetaType.Int,    "integer", 10),
                    QgsField("area_m2",     QMetaType.Double, "double", 20, 6)
                ])
                vl.updateFields()

                feats = []
                for cluster_id, n_points, area, wkt in self.clusters:
                    feat = QgsFeature()
                    feat.setGeometry(QgsGeometry.fromWkt(wkt))
                    feat.setAttributes([cluster_id, n_points, area])
                    feats.append(feat)
                pr.addFeatures(feats)

                vl.updateExtents()
                vl.commitChanges()

                symbol = QgsFillSymbol.createSimple({
                    "color": "0,0,255,50",          # Blue w/ ~20% opacity
                    "outline_color": "0,0,0,100",
                    "outline_width": "0.4"
                })
                vl.renderer().setSymbol(symbol)

                expr = "concat('ID: ', cluster_id, '\nArea: ', round(area_m2,1), ' m²')"
                vl.setDisplayExpression(expr)

                if self.output_path:
                    options = QgsVectorFileWriter.SaveVectorOptions()
                    options.driverName = QgsVectorFileWriter.driverForExtension(
                        os.path.splitext(self.output_path)[1].lstrip(".")
                    )

                    error_code, _, _, errorMessage = QgsVectorFileWriter.writeAsVectorFormatV3(
                        vl,
                        self.output_path,
                        QgsCoordinateTransformContext(),
                        options
                    )

                    if error_code == QgsVectorFileWriter.NoError:
                        vl.setName(layer_name)
                        if self.output_path.lower().endswith(".gpkg"):
                            vl.saveStyleToDatabase("default", "Detected building style", True,"")
                    else:
                        QgsMessageLog.logMessage(
                            f"{self.tr('Error saving output file')}: {errorMessage}",
                            "MyLiDAR",
                            Qgis.Critical
                        )

                QgsProject.instance().addMapLayer(vl)

                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Building Detection Complete"),
                    f"{self.tr('Building points detected')}: {self.num_points:,}\n"
                    f"{self.tr('Approximate number of buildings detected')}: {self.num_buildings:,}"
                )

        else:
            msg = f"{self.tr('An error occurred')}: {self.exception}" if self.exception else self.tr("Building detection failed")
            QgsMessageLog.logMessage(msg, "MyLiDAR", Qgis.Critical)
            QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error Detecting Buildings"), msg)

        if self in self.parent.running_tasks:
            self.parent.running_tasks.remove(self)

        else:
            msg = f"{self.tr('An error occurred')}: {self.exception}" if self.exception else self.tr("Building detection failed")
            QgsMessageLog.logMessage(msg, "MyLiDAR", Qgis.Critical)
            QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error Detecting Buildings"), msg)

        if self in self.parent.running_tasks:
            self.parent.running_tasks.remove(self)

# ----------------------------------
# --- Main Building Count Method ---
# ----------------------------------

def count_buildings(self):
    # Stem 1: Select input/output and parameters
    dialog = BuildingCountDialog(self.iface.mainWindow(), tr=self.tr)
    if not dialog.exec_():
        return

    input_filename, output_filename = dialog.get_input_output()
    if not input_filename:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Input Selected"),
            self.tr("Please select a LiDAR layer or file.")
        )
        return

    eps, min_samples, use_z = dialog.get_params()

    if not input_filename:
        QMessageBox.warning(self.iface.mainWindow(), self.tr("Missing Input"), self.tr("Please select a LiDAR input file or layer."))
        return

    # Step 2: Create and run the background task
    task_desc = f"{self.tr('Counting buildings in')} {os.path.basename(input_filename)}"
    task = BuildingCountTask(task_desc, input_filename, eps, min_samples, use_z, self, self.tr, output_filename)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Detecting buildings in the background"),
        level=Qgis.Info,
        duration=-1
    )
