from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './dem_generation_form.ui'))

class DemGenerationDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.setupUi(self)
        self.tr = translator if translator else (lambda s: s)

        self.setWindowTitle(self.tr("Bare Earth DEM Settings"))
        self.label.setText(self.tr("Enter DEM cell size (meters):"))
        self.cellSizeSpinBox.setToolTip(self.tr("Specify the cell size for the generated DEM in meters. The smaller the cell size, the higher its resolution and detail, but it may also increase processing time and file size"))

        self.triangulationCheckBox.setText(self.tr("Use triangulation (TIN) interpolation"))
        self.triangulationCheckBox.setToolTip(self.tr("Warning: This method takes significantly longer to process. For large areas, consider using the default griddata interpolation method for faster results"))

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def get_values(self):
        cell_size = self.cellSizeSpinBox.value()
        use_triangulation = self.triangulationCheckBox.isChecked()
        return cell_size, use_triangulation
