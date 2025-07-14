def classFactory(iface):
    # from .lidar_processing_plugin import LidarProcessingPlugin
    # return LidarProcessingPlugin(iface)

    from .doc_plugin import DocumentGenerationPlugin
    return DocumentGenerationPlugin(iface)
