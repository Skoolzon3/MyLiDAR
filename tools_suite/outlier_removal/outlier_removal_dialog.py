from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './outlier_removal_form.ui'))

class OutlierRemovalDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.setupUi(self)

        self.tr = translator if translator else (lambda s: s)

        self.setWindowTitle(self.tr("Outlier Removal Settings"))
        self.labelRadius.setText(self.tr("Search Radius (units):"))
        self.spinRadius.setToolTip(self.tr("Neighborhood search radius. Points with too few neighbors within this radius are considered outliers"))
        self.labelNeighbors.setText(self.tr("Minimum Neighbors:"))
        self.spinMinNeighbors.setToolTip(self.tr("Minimum number of neighbors required within the radius to retain a point. Points with fewer are removed as outliers"))

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def get_values(self):
        radius = self.spinRadius.value()
        min_neighbors = self.spinMinNeighbors.value()
        return radius, min_neighbors

