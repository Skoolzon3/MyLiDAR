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

# --- Dialog imports ---
from .feature_count_dialog import FeatureCountDialog

# --- Utility imports ---
from ..utils import log_step

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

    def __init__(self, description, input_filename, eps, min_samples, use_z, hull_target_percent, hull_allow_holes, parent, translator, feature_types, output_paths=None, log_filename=None):
        super().__init__(description, QgsTask.CanCancel)

        self.input_filename = input_filename
        self.eps = eps
        self.min_samples = min_samples
        self.use_z = use_z
        self.hull_target_percent = hull_target_percent
        self.hull_allow_holes = hull_allow_holes
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
        self.log_filename = log_filename
        self.log_entries = []

    def run(self):
        try:
            log_step(self, self.tr("PROCESS START"), f"Input: {os.path.basename(self.input_filename)}, EPS: {self.eps}, MinPts: {self.min_samples}, Use Z: {self.use_z}")

            # Step 1: Read input file
            log_step(self, self.tr("READING INPUT FILE"), self.input_filename, "info")
            las = laspy.read(self.input_filename, laz_backend=LazBackend.Lazrs)
            pycrs = las.header.parse_crs(prefer_wkt=True)
            if pycrs:
                self.output_crs = QgsCoordinateReferenceSystem(pycrs.to_wkt())
                log_step(self, self.tr("CRS DETECTED"), f"From file header: {self.output_crs.authid()}", "info")
            else:
                log_step(self, self.tr("CRS NOT FOUND"), self.tr("No CRS found in file header. Checking input layer loaded in QGIS"), "warning")

                matched_layer = None
                for lyr in QgsProject.instance().mapLayers().values():
                    if isinstance(lyr, QgsPointCloudLayer) and lyr.source() == self.input_filename:
                        matched_layer = lyr
                        break

                if matched_layer:
                    if matched_layer.crs().isValid():
                        self.output_crs = matched_layer.crs()
                        log_step(self, self.tr("CRS ASSIGNED"), f"{self.tr('Using CRS assigned in QGIS')}: {self.output_crs.authid()}", "info")
                    else:
                        log_step(self, self.tr("INVALID CRS"), self.tr("Matched layer CRS is invalid, no CRS will be assigned"), "warning")

                else:
                    log_step(self, self.tr("NO LAYER MATCH"), self.tr("Input file not found among loaded layers. Cannot import CRS from QGIS"), "warning")

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

            log_step(self, self.tr("FILTERING POINTS"), f"Filtering for feature types: {', '.join(self.feature_types)}", "info")
            for ftype in self.feature_types:
                feature_class_codes = class_map.get(ftype)
                if not feature_class_codes:
                    continue
                classifications = las.classification
                is_feature = np.isin(classifications, feature_class_codes)
                log_step(self, self.tr("POINTS FILTERED"), f"{ftype.capitalize()}: {np.sum(is_feature)} points", "info")

                num_points = int(np.sum(is_feature))
                self.results[ftype]["num_points"] = num_points

                if num_points == 0:
                    continue
                self.setProgress(20)

                # Step 3: Extract coordinates for clustering
                if self.use_z:
                    coords = np.vstack((las.x[is_feature], las.y[is_feature], las.z[is_feature])).T
                    log_step(self, self.tr("COORDINATES EXTRACTED"), f"Using X, Y, Z for clustering")
                else:
                    coords = np.vstack((las.x[is_feature], las.y[is_feature])).T
                    log_step(self, self.tr("COORDINATES EXTRACTED"), f"Using X, Y for clustering")
                self.setProgress(30)

                # Step 4: DBSCAN clustering
                db = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(coords)
                labels = db.labels_
                num_features = len(set(labels)) - (1 if -1 in labels else 0)
                self.results[ftype]["num_features"] = num_features
                log_step(self, self.tr("CLUSTERING COMPLETE"), f"{ftype.capitalize()}: {num_features} features detected", "info")
                self.setProgress(70)

                # Step 5: Concave hulls for clusters
                log_step(self, self.tr("GENERATING HULLS"), f"Generating hulls for {ftype} clusters", "info")
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

                    hull_geom = geom_pts.concaveHull(self.hull_target_percent, self.hull_allow_holes)
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

            log_step(self, self.tr("PROCESS COMPLETE"), f"Total points processed: {las.header.point_count}, Total features detected: {sum(r['num_features'] for r in self.results.values())}", "info")
            self.total_points = int(las.header.point_count)
            self.setProgress(100)
            return True

        except Exception as e:
            log_step(self, self.tr("PROCESS FAILED"), f"Error: {str(e)}", "critical")
            self.exception = e
            return False

    def finished(self, result):
        if result:
            # Task completed successfully
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
                    QgsField("cluster_id", QMetaType.Type.Int),
                    QgsField("num_points", QMetaType.Type.Int),
                    QgsField("area_m2", QMetaType.Type.Double, "double", 20, 6),
                    QgsField("est_h_m", QMetaType.Type.Double, "double", 20, 3)
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
                                log_step(self, self.tr("GPKG VALIDATION FAILED"), f"Failed to load GPKG layer for validation: {out_path}", "critical")
                            else:
                                field_names = [field.name() for field in gpkg_layer.fields()]
                                expected_fields = ["cluster_id", "num_points", "area_m2"]
                                missing = [f for f in expected_fields if f not in field_names]
                                present = [f for f in expected_fields if f in field_names]
                                log_step(self, self.tr("GPKG ATTRIBUTE CHECK"), f"Present: {present}, Missing: {missing}", "info")
                            gpkg_layer.saveStyleToDatabaseV2(
                                "default", "Detected building style", True, ""
                            )
                    else:
                        log_step(self, self.tr("FILE SAVE ERROR"), f"{self.tr('Error saving output file')}: {errorMessage}", "critical")

                QgsProject.instance().addMapLayer(vl)
                QMessageBox.information(
                    self.parent.iface.mainWindow(),
                    self.tr("Feature Detection Complete"),
                    f"{self.tr(ftype.capitalize())}:\n"
                    f"{self.tr('Points detected')}: {data['num_points']:,}\n"
                    f"{self.tr('Approximate number of features detected')}: {data['num_features']:,}"
                )

        else:
            if self.exception:
                log_step(self, self.tr("ERROR EXCEPTION"), f"{self.tr('An error occurred during feature detection')}: {self.exception}", "critical")
                QMessageBox.critical(self.parent.iface.mainWindow(), self.tr("Error Detecting Features"), f"{self.tr('An error occurred')}:\n{self.exception}")
            else:
                log_step(self, self.tr("TASK CANCELED"), self.tr('Point filtering was canceled by the user'), "info")

        if self.log_filename:
            try:
                with open(self.log_filename, 'w', encoding='utf-8') as f:
                    f.write(f"MyLiDAR FEATURE COUNT REPORT\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Input file: {self.input_filename}\n")
                    f.write(f"Output files: {', '.join(self.output_paths.values()) if self.output_paths else 'None'}\n")
                    f.write(f"Clustering parameters: EPS={self.eps}, MinPts={self.min_samples}, Use Z={self.use_z}\n")
                    f.write(f"CRS: {self.output_crs.authid() if self.output_crs else 'Not set'}\n")
                    f.write(f"Total points processed: {self.total_points}\n")
                    f.write(f"Total features detected: {sum(r['num_features'] for r in self.results.values())}\n\n")
                    f.write("PROCESSING STEPS:\n")
                    f.write("-" * 30 + "\n")
                    for entry in self.log_entries:
                        f.write(entry + "\n")

                    if not result and self.exception:
                        f.write(f"\nFINAL STATUS: FAILED\nError: {str(self.exception)}\n")
                    else:
                        f.write(f"\nFINAL STATUS: SUCCESS\n")

                log_step(self, self.tr("LOG FILE WRITTEN"), self.log_filename, "info")

            except Exception as log_error:
                QgsMessageLog.logMessage(
                    f"Failed to write log file {self.log_filename}: {log_error}",
                    "MyLiDAR", Qgis.Warning
                )

        if self in self.parent.running_tasks:
            self.parent.running_tasks.remove(self)

# ----------------------------------
# --- Main Feature Count Method ---
# ----------------------------------

def _count_features_accepted(self):
    dialog = self.dialog

    # Step 1: Select input/output and parameters
    input_filename, output_map  = dialog.get_input_output()
    if not input_filename:
        QMessageBox.warning(
            self.iface.mainWindow(),
            self.tr("No Input Selected"),
            self.tr("Please select a LiDAR layer or file.")
        )
        return
    
    log_filename = dialog.get_log_path()

    eps, min_samples, use_z, hull_target_percent, hull_allow_holes = dialog.get_params()
    feature_types = dialog.get_feature_types()

    if not input_filename:
        QMessageBox.warning(self.iface.mainWindow(), self.tr("Missing Input"), self.tr("Please select a LiDAR input file or layer."))
        return

    if not feature_types:
        QMessageBox.warning(self.iface.mainWindow(), self.tr("No Feature Types"), self.tr("Please select at least one feature type to detect."))
        return

    # Step 2: Create and run the background task
    task_desc = f"{self.tr('Counting features in')} {os.path.basename(input_filename)}"
    task = FeatureCountTask(task_desc, input_filename, eps, min_samples, use_z, hull_target_percent, hull_allow_holes, self, self.tr, feature_types, output_paths=output_map, log_filename=log_filename)

    self.running_tasks.append(task)
    QgsApplication.taskManager().addTask(task)

    self.iface.messageBar().pushMessage(
        self.tr("Task Started"),
        self.tr("Detecting features in the background"),
        level=Qgis.Info,
        duration=-1
    )

def count_features(self):
    self.dialog = FeatureCountDialog(self.iface.mainWindow(), tr=self.tr)
    self.dialog.accepted.connect(lambda: _count_features_accepted(self))
    self.dialog.show()
    self.dialog.raise_()
    self.dialog.activateWindow()