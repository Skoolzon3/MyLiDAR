def classFactory(iface):
    from .lidar_processing_plugin import LidarProcessingPlugin
    return LidarProcessingPlugin(iface)
