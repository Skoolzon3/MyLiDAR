def ensure_dependencies():
    import importlib, subprocess, sys

    packages = ["laspy", "scipy", "GDAL", "OSR", "matplotlib", "reportlab", "scikit-learn"]
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def classFactory(iface):
    ensure_dependencies()

def classFactory(iface):
    from .my_lidar import MyLiDARPlugin
    return MyLiDARPlugin(iface)
