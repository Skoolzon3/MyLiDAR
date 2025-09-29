from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), './building_count_form.ui'))

class BuildingParamsDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.setupUi(self)
        self.tr = translator if translator else (lambda s: s)

        self.setWindowTitle(self.tr("Building Detection Parameters"))
        self.label_eps.setText(self.tr("DBSCAN Epsilon:"))
        self.epsSpin.setToolTip(self.tr("Maximum distance between points to be considered neighbors"))

        self.label_min_samples.setText(self.tr("Min Samples:"))
        self.minSamplesSpin.setToolTip(self.tr("Minimum number of points required to form a cluster"))

        self.useZCheck.setText(self.tr("Use Z-axis for clustering (3D)"))
        self.useZCheck.setToolTip(self.tr(
            "Clustering will consider height (Z) as well as X and Y. "
            "This may improve building detection in areas with varying terrain"
        ))

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def get_params(self):
        eps = self.epsSpin.value()
        min_samples = self.minSamplesSpin.value()
        use_z = self.useZCheck.isChecked()
        return eps, min_samples, use_z
