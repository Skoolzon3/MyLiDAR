import os
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import QgsRasterLayer, QgsProject

class LidarProcessingPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = 'LiDAR Processor'
        self.icon_path = os.path.join(self.plugin_dir, 'icon.png')

    def initGui(self):
        # Add action to menu
        self.action_process = QAction('Process LiDAR Data', self.iface.mainWindow())
        self.action_process.triggered.connect(self.process_lidar)
        self.iface.addPluginToMenu(self.menu, self.action_process)
        self.actions.append(self.action_process)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)

    def process_lidar(self):
        # Let user pick LAS/LAZ file
        las_file, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            'Select LiDAR LAS/LAZ file',
            '',
            'LAS/LAZ Files (*.las *.laz)'
        )
        if not las_file:
            return

        # Output file for classified data
        output_file = os.path.splitext(las_file)[0] + '_classified.las'

        # PDAL pipeline JSON (classify ground)
        pipeline_json = f"""
        {{
            "pipeline": [
                "{las_file}",
                {{
                    "type": "filters.smrf",
                    "ignore": "Classification[7:7]",
                    "scalar": 1.2,
                    "slope": 0.2,
                    "threshold": 0.45,
                    "window": 16.0
                }},
                {{
                    "type": "writers.las",
                    "filename": "{output_file}"
                }}
            ]
        }}
        """

        try:
            import pdal
        except ImportError:
            QMessageBox.critical(self.iface.mainWindow(), "PDAL Missing!", "The PDAL Python bindings are not installed.")
            return

        # Run PDAL
        try:
            pipeline = pdal.Pipeline(pipeline_json)
            pipeline.execute()
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "PDAL Error", str(e))
            return

        # Generate DEM from ground points
        dem_file = os.path.splitext(las_file)[0] + '_dem.tif'
        dem_pipeline_json = f"""
        {{
            "pipeline": [
                "{output_file}",
                {{
                    "type":"filters.range",
                    "limits":"Classification[2:2]"
                }},
                {{
                    "type":"writers.gdal",
                    "filename":"{dem_file}",
                    "resolution":1.0,
                    "output_type":"idw"
                }}
            ]
        }}
        """
        try:
            dem_pipeline = pdal.Pipeline(dem_pipeline_json)
            dem_pipeline.execute()
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "DEM Generation Error", str(e))
            return

        # Load DEM into QGIS
        raster_layer = QgsRasterLayer(dem_file, os.path.basename(dem_file))
        if not raster_layer.isValid():
            QMessageBox.warning(self.iface.mainWindow(), "Layer Error", "Failed to load generated DEM.")
            return

        QgsProject.instance().addMapLayer(raster_layer)
        QMessageBox.information(self.iface.mainWindow(), "Success", "LiDAR processing complete!")
