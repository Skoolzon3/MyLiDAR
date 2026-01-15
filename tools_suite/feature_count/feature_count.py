# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsField, QgsProject, QgsFillSymbol, QgsTask, QgsApplication, Qgis, QgsMessageLog, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsPointCloudLayer, QgsPointXY

from qgis.PyQt.QtCore import QMetaType

# --- Method-specific imports ---
from sklearn.cluster import DBSCAN
from shapely.geometry import MultiPoint

# --- Dialog imports ---
from .feature_count_dialog import FeatureCountDialog

# ---------------------
# --- Feature Count ---
# -----------------------------------------------------------------------------------------------
# Description:
# This function counts features in LiDAR point clouds through DBSCAN clustering on building and
# vegetation-classified points, providing an approximate count of features based on its results.
# Users can specify parameters for clustering (eps and min_samples).
# -----------------------------------------------------------------------------------------------

# ------------------------------------------
# --- Background Task for Feature Count ---
# ------------------------------------------

class FeatureCountTask(QgsTask):
    """Background task for counting features using DBSCAN on LiDAR data"""

    def __init__(self, description, input_filename, eps, min_samples, use_z, parent, translator, feature_types, output_paths=None):
        super().__init__(description, QgsTask.CanCancel)

        self.input_filename = input_filename
        self.eps = eps
        self.min_samples = min_samples
        self.use_z = use_z
        self.parent = parent
        self.output_paths = output_paths or {}
        self.feature_types = feature_types

        self.tr = translator
        self.exception = None

        self.num_features = 0
        self.num_points = 0
        self.total_points = 0
        self.output_crs = None
        self.results = {
            "buildings": {"clusters": [], "num_points": 0, "num_features": 0},
            "trees": {"clusters": [], "num_points": 0, "num_features": 0},
            "bridges": {"clusters": [], "num_points": 0, "num_features": 0}
        }

    def run(self):
        try:
            # Step 1: Read input file
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            pycrs = las.header.parse_crs(prefer_wkt=True)
            if pycrs:
                self.output_crs = QgsCoordinateReferenceSystem(pycrs.to_wkt())
            else:
                QgsMessageLog.logMessage(
                    self.tr("No CRS found in file header. Checking input layer loaded in QGIS"),
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
                            f"{self.tr('Using CRS assigned in QGIS')}: {self.output_crs.authid()}",
                            "MyLiDAR", Qgis.Info
                        )
                    else:
                        QgsMessageLog.logMessage(
                            self.tr("Matched layer CRS is invalid, no CRS will be assigned"),
                            "MyLiDAR", Qgis.Warning
                        )
                else:
                    QgsMessageLog.logMessage(
                        self.tr("Input file not found among loaded layers. Cannot import CRS from QGIS"),
                        "MyLiDAR", Qgis.Warning
                    )
            self.setProgress(10)

            for ftype in self.feature_types:
                self.results[ftype] = {
                    "clusters": [],
                    "num_points": 0,
                    "num_features": 0
                }

            # Step 2: Filter building-classified points
            class_map = {
                "buildings": [6],
                "trees": [5],
                "bridges": [17]
            }

            for ftype in self.feature_types:
                feature_class_codes = class_map.get(ftype)
                if not feature_class_codes:
                    continue
                classifications = las.classification
                is_feature = np.isin(classifications, feature_class_codes)

                num_points = int(np.sum(is_feature))
                self.results[ftype]["num_points"] = num_points

                if num_points == 0:
                    continue
                self.setProgress(20)

                # Step 3: Extract coordinates for clustering
                if self.use_z:
                    coords = np.vstack((las.x[is_feature], las.y[is_feature], las.z[is_feature])).T
                else:
                    coords = np.vstack((las.x[is_feature], las.y[is_feature])).T
                self.setProgress(30)

                # Step 4: DBSCAN clustering
                db = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(coords)
                labels = db.labels_
                num_features = len(set(labels)) - (1 if -1 in labels else 0)
                self.results[ftype]["num_features"] = num_features
                self.setProgress(70)

                # Step 5: Concave hulls for clusters
                unique_clusters = [cid for cid in set(labels) if cid != -1]
                total_clusters = len(unique_clusters)

                for idx, cluster_id in enumerate(unique_clusters, start=1):
                    if self.isCanceled():
                        return False

                    cluster_coords = coords[labels == cluster_id]
                    if len(cluster_coords) < self.min_samples:
                        continue

                    if self.use_z:
                        points_xy = [QgsPointXY(float(x), float(y)) for x, y, _z in cluster_coords]
                    else:
                        points_xy = [QgsPointXY(float(x), float(y)) for x, y in cluster_coords]

                    geom_pts = QgsGeometry.fromMultiPointXY(points_xy)
                    target_percent = 0.2 # 0 = very concave, 1 = convex
                    allow_holes = True

                    hull_geom = geom_pts.concaveHull(target_percent, allow_holes)
                    if hull_geom.isEmpty():
                        continue

                    poly = hull_geom

                    if self.use_z:
                        z_vals = cluster_coords[:, 2]
                        height_est = float(z_vals.max() - z_vals.min())
                    else:
                        height_est = 0.0

                    self.results[ftype]["clusters"].append((
                        int(cluster_id),
                        len(cluster_coords),
                        poly.area(),
                        poly.asWkt(),
                        height_est,
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

            base_name = os.path.splitext(os.path.basename(self.input_filename))[0]
            cluster_suffix = "3D_clustering" if self.use_z else "2D_clustering"

            for ftype, data in self.results.items():

                if data["num_points"] == 0:
                    continue

                layer_name = f"{base_name}_{ftype}_{cluster_suffix}"

                vl = QgsVectorLayer("Polygon", layer_name, "memory")
                pr = vl.dataProvider()

                if self.output_crs and self.output_crs.isValid():
                    vl.setCrs(self.output_crs)
                else:
                    vl.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))

                pr.addAttributes([
                    QgsField("cluster_id", QMetaType.Int),
                    QgsField("num_points", QMetaType.Int),
                    QgsField("area_m2", QMetaType.Double, "double", 20, 6),
                    QgsField("est_h_m", QMetaType.Double, "double", 20, 3)
                ])
                vl.updateFields()

                feats = []
                for cluster_id, n_points, area, wkt, height_est in data["clusters"]:
                    feat = QgsFeature()
                    feat.setGeometry(QgsGeometry.fromWkt(wkt))
                    feat.setAttributes([cluster_id, n_points, area, height_est])
                    feats.append(feat)

                pr.addFeatures(feats)
                vl.updateExtents()
                vl.commitChanges()

                if ftype == "trees":
                    fill_color = "0,255,0,50"
                elif ftype == "buildings":
                    fill_color = "0,0,255,50"
                else:
                    fill_color = "255,0,0,50"

                symbol = QgsFillSymbol.createSimple({
                    "color": fill_color,
                    "outline_color": "0,0,0,100",
                    "outline_width": "0.4"
                })

                vl.renderer().setSymbol(symbol)

                vl.setDisplayExpression("concat('ID: ', cluster_id, '\nArea: ', round(area_m2,1), ' m²', '\nHeight: ', round(est_h_m,1), ' m')")

                out_path = self.output_paths.get(ftype)
                if out_path:
                    options = QgsVectorFileWriter.SaveVectorOptions()
                    options.driverName = QgsVectorFileWriter.driverForExtension(
                        os.path.splitext(out_path)[1].lstrip(".")
                    )

                    options.includeFields = True
                    options.symbologyExport = QgsVectorFileWriter.SymbologyExport.SymbolLayerSymbology
                    options.layerName = layer_name  # !

                    error_code, _, _, errorMessage = QgsVectorFileWriter.writeAsVectorFormatV3(
                        vl,
                        out_path,
                        QgsCoordinateTransformContext(),
                        options
                    )

                    if error_code == QgsVectorFileWriter.NoError:
                        vl.setName(layer_name)

                        if out_path.lower().endswith(".gpkg"):
                            gpkg_layer = QgsVectorLayer(out_path, layer_name, "ogr")

                            if not gpkg_layer.isValid():
                                QgsMessageLog.logMessage(
                                    "Failed to reload GPKG layer for validation",
                                    "MyLiDAR",
                                    Qgis.Critical
                                )
                            else:
                                field_names = [field.name() for field in gpkg_layer.fields()]
                                expected_fields = ["cluster_id", "num_points", "area_m2"]

                                missing = [f for f in expected_fields if f not in field_names]
                                present = [f for f in expected_fields if f in field_names]

                                QgsMessageLog.logMessage(
                                    f"GPKG attribute check — Present: {present}, Missing: {missing}",
                                    "MyLiDAR",
                                    Qgis.Info
                                )

                            gpkg_layer.saveStyleToDatabaseV2(
                                "default", "Detected building style", True, ""
                            )

                    else:
                        QgsMessageLog.logMessage(
                            f"{self.tr('Error saving output file')}: {errorMessage}",
                            "MyLiDAR",
                            Qgis.Critical
                        )

                QgsProject.instance().addMapLayer(vl)

                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Feature Detection Complete"),
                    f"{self.tr(ftype.capitalize())}:\n"
                    f"{self.tr('Points detected')}: {data['num_points']:,}\n"
                    f"{self.tr('Approximate number of features detected')}: {data['num_features']:,}"
                )

        else:
            msg = f"{self.tr('An error occurred')}: {self.exception}" if self.exception else self.tr("Feature detection failed")
            QgsMessageLog.logMessage(msg, "MyLiDAR", Qgis.Critical)
            QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error Detecting Features"), msg)

        if self in self.parent.running_tasks:
            self.parent.running_tasks.remove(self)

# ----------------------------------
# --- Main Feature Count Method ---
# ----------------------------------

def count_features(self):
    # Stem 1: Select input/output and parameters
    dialog = FeatureCountDialog(self.iface.mainWindow(), tr=self.tr)
    if not dialog.exec_():
        return

    input_filename, output_map  = dialog.get_input_output()
    if not input_filename:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Input Selected"),
            self.tr("Please select a LiDAR layer or file.")
        )
        return

    eps, min_samples, use_z = dialog.get_params()
    feature_types = dialog.get_feature_types()

    if not input_filename:
        QMessageBox.warning(self.iface.mainWindow(), self.tr("Missing Input"), self.tr("Please select a LiDAR input file or layer."))
        return

    # Step 2: Create and run the background task
    task_desc = f"{self.tr('Counting features in')} {os.path.basename(input_filename)}"
    task = FeatureCountTask(task_desc, input_filename, eps, min_samples, use_z, self, self.tr, feature_types, output_paths=output_map)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Detecting features in the background"),
        level=Qgis.Info,
        duration=-1
    )
