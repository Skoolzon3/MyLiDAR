from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './vegetation_classification_form.ui'))

class VegetationClassificationDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def get_values(self):
        low_thresh = self.spinLow.value()
        high_thresh = self.spinHigh.value()
        return low_thresh, high_thresh
