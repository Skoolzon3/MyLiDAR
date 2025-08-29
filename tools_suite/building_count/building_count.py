# --- General imports ---
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtTest import QTest
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsField, QgsProject, QgsFillSymbol
from PyQt5.QtCore import Qt, QVariant

# --- Method-specific imports ---
from sklearn.cluster import DBSCAN
from shapely.geometry import MultiPoint

# --- Dialog imports ---
from ...utils import create_loading_dialog
from .building_count_dialog import BuildingParamsDialog

# ----------------------
# --- Building Count ---
# ----------------------
# Description:
# This function counts buildings in LiDAR point clouds through DBSCAN clustering
# on building-classified points, providing an approximate count of buildings based on its results.
# Users can specify parameters for clustering (eps and min_samples).
# ----------------------

def count_buildings(self):
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File to Count Buildings',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not filename:
        return

    param_dialog = BuildingParamsDialog(self.iface.mainWindow())
    if not param_dialog.exec_():
        return

    eps, min_samples = param_dialog.get_params()

    loading_dialog = create_loading_dialog(self, message="Counting buildings...")

    try:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        loading_dialog.show()
        QApplication.processEvents()
        QTest.qWait(100)

        las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

        # Filter building-classified points
        building_class_code = 6
        classifications = las.classification
        is_building = classifications == building_class_code

        if np.sum(is_building) == 0:
            QMessageBox.information(
                self.iface.mainWindow(),
                "No Buildings Found",
                "No buildings were found in this file."
            )
            return

        # Extract X and Y for clustering
        coords = np.vstack((las.x[is_building], las.y[is_building])).T
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
        labels = db.labels_

        # Count clusters (excluding noise points labeled -1)
        num_buildings = len(set(labels)) - (1 if -1 in labels else 0)

        # --- QGIS polygon layer ---
        crs = None
        try:
            crs = las.header.parse_crs().to_epsg()
        except Exception:
            crs = 4326  # fallback if CRS not defined

        vl = QgsVectorLayer(f"Polygon?crs=EPSG:{crs}", "Detected_Buildings", "memory")
        pr = vl.dataProvider()
        pr.addAttributes([
            QgsField("cluster_id", QVariant.Int),
            QgsField("num_points", QVariant.Int),
            QgsField("area_m2", QVariant.Double)
        ])
        vl.updateFields()

        for cluster_id in set(labels):
            if cluster_id == -1:
                continue

            cluster_coords = coords[labels == cluster_id]

            if len(cluster_coords) < min_samples:
                continue

            # Convex hull polygon of the cluster
            poly = MultiPoint(cluster_coords).convex_hull
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromWkt(poly.wkt))
            feat.setAttributes([int(cluster_id), len(cluster_coords), poly.area])
            pr.addFeature(feat)
            symbol = QgsFillSymbol.createSimple({
                'color': '0,0,255,50',          # Blue w/ alpha=50 (~20% opacity)
                'outline_color': '0,0,0,100',
                'outline_width': '0.4'
            })
            vl.renderer().setSymbol(symbol)

            # Expression displayed when hovering over polygons (PD: View → Map Tips must be enabled)
            expr = "concat('ID: ', cluster_id, '\nArea: ', round(area_m2,1), ' m²')"
            vl.setDisplayExpression(expr)

        QgsProject.instance().addMapLayer(vl)

        QMessageBox.information(
            self.iface.mainWindow(),
            "Building Detection Complete",
            f"Building points detected: {np.sum(is_building):,}\n"
            f"Approximate number of building detected: {num_buildings:,}"
        )

    except Exception as e:
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Error Detecting Buildings",
            f"An error occurred:\n{e}"
        )

    finally:
        loading_dialog.close()
        QApplication.restoreOverrideCursor()
