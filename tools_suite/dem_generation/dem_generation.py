# --- General imports ---
import os
import laspy
from laspy import LazBackend
import numpy as np

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QDialog
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from qgis.core import QgsProject, QgsRasterLayer, QgsProcessingException
import processing

# --- Method-specific imports ---
from osgeo import gdal, osr
from scipy.interpolate import griddata

# --- Dialog imports ---
from .dem_generation_dialog import DemGenerationDialog
from ...utils import create_loading_dialog

# ---------------------------------
# --- Bare Earth DEM Generation ---
# ---------------------------------
# Description:
# This function generates a bare earth DEM from LiDAR point clouds by filtering ground points,
# creating a raster grid and filling gaps using nearest-neighbor interpolation.
# It allows users to specify the cell size for the DEM.
# ---------------------------------

def generate_bare_earth_dem(self):
    filename, _ = QFileDialog.getOpenFileName(
        self.iface.mainWindow(),
        'Select LiDAR File for Bare Earth DEM',
        '',
        'LiDAR Files (*.las *.laz)'
    )
    if not filename:
        return

    dlg = DemGenerationDialog(self.iface.mainWindow())
    if dlg.exec_() != QDialog.Accepted:
        return
    cell_size, use_triangulation = dlg.get_values()

    loading_dialog = create_loading_dialog(self, message="Generating Bare Earth DEM...")

    try:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        loading_dialog.show()
        QApplication.processEvents()
        QTest.qWait(100)

        las = laspy.read(filename, laz_backend=LazBackend.Lazrs)

        ground_mask = (las.classification == 2)  # Filter ground points
        if not np.any(ground_mask):
            raise ValueError("No ground points found in the file.")

        x = las.x[ground_mask]
        y = las.y[ground_mask]
        z = las.z[ground_mask]
        min_x, max_x = x.min(), x.max()
        min_y, max_y = y.min(), y.max()
        cols = int(np.ceil((max_x - min_x) / cell_size))
        rows = int(np.ceil((max_y - min_y) / cell_size))

        srs = osr.SpatialReference()
        try:
            from laspy.vlrs.known import WktCoordinateSystemVlr
            wkt_vlrs = [vlr for vlr in las.header.vlrs if isinstance(vlr, WktCoordinateSystemVlr)]
            if wkt_vlrs:
                srs.ImportFromWkt(wkt_vlrs[0].wkt)
            else:
                srs.ImportFromEPSG(4326)
        except Exception:
            srs.ImportFromEPSG(4326)

        # --- DEM Generation ---
        if use_triangulation:
            # Triangulation-based interpolation (TIN)
            grid_x, grid_y = np.meshgrid(
                np.linspace(min_x, max_x, cols),
                np.linspace(min_y, max_y, rows)
            )

            dem = griddata(
                (x, y), z,
                (grid_x, grid_y),
                method='linear'
            )

            # Fallback: fill gaps with nearest-neighbor
            dem = np.where(
                np.isnan(dem),
                griddata((x, y), z, (grid_x, grid_y), method='nearest'),
                dem
            )

        else:
            # Minimum-Z rasterization (bare earth assumption)
            dem = np.full((rows, cols), np.nan, dtype=np.float32)

            col_idx = ((x - min_x) / cell_size).astype(int)
            row_idx = ((max_y - y) / cell_size).astype(int)  # Flip Y for raster

            # Assign minimum Z to each cell (bare earth assumption)
            for r, c, z_val in zip(row_idx, col_idx, z):
                if 0 <= r < rows and 0 <= c < cols:
                    if np.isnan(dem[r, c]) or z_val < dem[r, c]:
                        dem[r, c] = z_val

        # Replace NaNs with -9999 (to mark nodata for GDAL)
        dem = np.where(np.isnan(dem), -9999, dem)

        output_path, _ = QFileDialog.getSaveFileName(
            self.iface.mainWindow(),
            'Save Bare Earth DEM',
            os.path.splitext(filename)[0] + '_bare_earth_dem.tif',
            'GeoTIFF (*.tif)'
        )
        if not output_path:
            return

        driver = gdal.GetDriverByName('GTiff')
        out_raster = driver.Create(output_path, cols, rows, 1, gdal.GDT_Float32)
        out_raster.SetGeoTransform((min_x, cell_size, 0, max_y, 0, -cell_size))

        out_raster.SetProjection(srs.ExportToWkt())
        out_band = out_raster.GetRasterBand(1)
        out_band.WriteArray(dem)
        out_band.SetNoDataValue(-9999)
        out_band.FlushCache()

        # Hybrid step: Fill Nodata gaps with GDAL’s FillNodata
        gdal.FillNodata(targetBand=out_band, maskBand=None,
                        maxSearchDist=10, smoothingIterations=1)

        # Update statistics
        dem_min, dem_max = float(np.nanmin(dem[dem != -9999])), float(np.nanmax(dem[dem != -9999]))
        out_band.ComputeStatistics(False)
        out_band.SetStatistics(dem_min, dem_max, 0, 0)

        out_raster = None  # Close dataset so GDAL can read it again

        reply = QMessageBox.question(
            self.iface.mainWindow(),
            "Generate Hillshade?",
            "Do you also want to create a hillshade raster from the DEM?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        hillshade_path = None
        if reply == QMessageBox.Yes:
            hillshade_path = os.path.splitext(output_path)[0] + '_hillshade.tif'
            try:
                processing_params = {
                    'INPUT': output_path,
                    'Z_FACTOR': 1.0,
                    'AZIMUTH': 315.0,
                    'V_ANGLE': 45.0,
                    'OUTPUT': hillshade_path
                }
                processing.run("native:hillshade", processing_params)
            except QgsProcessingException as e:
                hillshade_path = None
                QMessageBox.warning(
                    self.iface.mainWindow(),
                    "Hillshade Generation Failed",
                    f"Could not generate hillshade. The DEM was saved successfully.\n\nError: {e}"
                )

        dem_layer_name = os.path.splitext(os.path.basename(output_path))[0]
        dem_layer = QgsRasterLayer(output_path, dem_layer_name)
        if dem_layer.isValid():
            QgsProject.instance().addMapLayer(dem_layer)

        if hillshade_path:
            hillshade_layer_name = os.path.splitext(os.path.basename(hillshade_path))[0]
            hillshade_layer = QgsRasterLayer(hillshade_path, hillshade_layer_name)
            if hillshade_layer.isValid():
                QgsProject.instance().addMapLayer(hillshade_layer)

        msg = f"DEM successfully generated from ground points.\nOutput saved at:\n{output_path}"
        if hillshade_path:
            msg += f"\n\nHillshade saved at:\n{hillshade_path}"

        QMessageBox.information(
            self.iface.mainWindow(),
            "Bare Earth DEM Generated",
            msg
        )

    except Exception as e:
        QMessageBox.critical(
            self.iface.mainWindow(),
            "Error whilst generating Bare Earth DEM",
            f"An error occurred:\n{e}"
        )

    finally:
        loading_dialog.close()
        QApplication.restoreOverrideCursor()
