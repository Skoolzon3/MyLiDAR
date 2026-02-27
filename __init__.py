import importlib
import subprocess
import sys
import os

def windows_dependencies():
    packages = {
        "laspy": "laspy",
        "scipy": "scipy",
        "osgeo.gdal": "gdal",
        "osgeo.osr": "gdal",
        "matplotlib": "matplotlib",
        "reportlab": "reportlab",
        "sklearn": "scikit-learn",
        "shapely": "shapely"
    }

    python_exe = sys.executable
    if not os.path.basename(python_exe).lower().startswith("python"):
        python_exe = "python"

    for mod_name, pip_name in packages.items():
        try:
            importlib.import_module(mod_name)
        except ImportError:
            try:
                subprocess.check_call([python_exe, "-m", "pip", "install", pip_name])
            except Exception as e:
                from qgis.PyQt.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Dependency installation failed",
                    f"Failed to install {pip_name}\n\nError: {e}")
                raise


def other_so_dependencies():
    from pip._internal.cli.main import main as pip_main

    packages = {
        "laspy": "laspy[lazrs,laszip]",
        "scipy": "scipy",
        "osgeo.gdal": None,
        "osgeo.osr": None,
        "matplotlib": "matplotlib",
        "reportlab": "reportlab",
        "sklearn": "scikit-learn",
        "shapely": "shapely"
    }
    
    for module_name, pip_name in packages.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            if pip_name is not None:
                pip_main(["install", "--upgrade", pip_name])


def ensure_dependencies():
    if sys.platform == "win32":
        windows_dependencies()
    else:
        other_so_dependencies()


def classFactory(iface):
    ensure_dependencies()
    from .my_lidar import MyLiDARPlugin
    return MyLiDARPlugin(iface)
