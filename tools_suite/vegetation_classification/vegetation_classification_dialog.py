from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './vegetation_classification_form.ui'))

class VegetationClassificationDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.setupUi(self)
        self.tr = translator if translator else (lambda s: s)

        self.setWindowTitle(self.tr("Vegetation Thresholds"))
        self.labelLow.setText(self.tr("Low Vegetation Threshold (m):"))
        self.labelHigh.setText(self.tr("High Vegetation Threshold (m):"))

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def get_values(self):
        low_thresh = self.spinLow.value()
        high_thresh = self.spinHigh.value()
        return low_thresh, high_thresh
