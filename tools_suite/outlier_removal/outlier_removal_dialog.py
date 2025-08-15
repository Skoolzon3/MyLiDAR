from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './outlier_removal_form.ui'))

class OutlierRemovalDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def get_values(self):
        radius = self.spinRadius.value()
        min_neighbors = self.spinMinNeighbors.value()
        return radius, min_neighbors
