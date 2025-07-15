def classFactory(iface):
    from .doc_plugin import DocumentGenerationPlugin
    # from .lidar_processing_plugin import LidarProcessingPlugin

    # return LidarProcessingPlugin(iface)
    return DocumentGenerationPlugin(iface)
