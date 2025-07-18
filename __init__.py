def classFactory(iface):
    from .my_lidar import MyLiDARPlugin
    return MyLiDARPlugin(iface)
