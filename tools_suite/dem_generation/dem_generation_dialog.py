from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './dem_generation_form.ui'))

class DemGenerationDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def get_values(self):
        cell_size = self.cellSizeSpinBox.value()
        use_triangulation = self.triangulationCheckBox.isChecked()
        return cell_size, use_triangulation
