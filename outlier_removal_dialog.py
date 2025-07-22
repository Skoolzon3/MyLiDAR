from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './plugin_ui/outlier_removal_form.ui'))

class OutlierRemovalDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def get_values(self):
        return self.spinRadius.value(), self.spinMinNeighbors.value()
