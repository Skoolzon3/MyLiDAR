from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './plugin_ui/building_count_form.ui'))

class BuildingParamsDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def get_params(self):
        eps = self.epsSpin.value()
        min_samples = self.minSamplesSpin.value()
        return eps, min_samples
