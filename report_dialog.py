# -----------------------
# --- UI Dialog Class ---
# -----------------------

import os
from qgis.PyQt.QtWidgets import QDialogButtonBox, QDialog
from qgis.PyQt import uic
from PyQt5.QtWidgets import QDialog

form_class, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "./plugin_ui/report_form.ui"))

class ReportDialog(QDialog, form_class):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.groupTime.toggled.connect(self.on_group_time_toggled)
        self.groupIntensity.toggled.connect(self.on_group_intensity_toggled)
        self.groupSpatial.toggled.connect(self.on_group_spatial_toggled)
        self.groupFileMetadata.toggled.connect(self.on_group_file_metadata_toggled)
        self.groupClassification.toggled.connect(self.on_group_classification_toggled)

        self.checkboxes = [
            # Metadata checkboxes
            self.checkFileName,
            self.checkFileSource,
            self.checkGlobalEncoding,
            self.checkSystemId,
            self.checkGenSoftware,
            self.checkVersion,
            self.checkPointFormat,
            self.checkCreationDate,

            # Intensity checkboxes
            self.checkMinIntensity,
            self.checkMaxIntensity,

            # Spatial bounds checkboxes
            self.checkNumPoints,
            self.checkArea,
            self.checkDensity,
            self.checkBounds,
            self.checkXAxisBounds,
            self.checkYAxisBounds,

            # GPS time checkboxes
            self.checkMinTime,
            self.checkMaxTime,

            # Point metrics checkboxes
            self.checkClassCounts,
            self.checkReturnCounts,
        ]

        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)

        for checkbox in self.checkboxes:
            checkbox.stateChanged.connect(self.update_ok_button)

        self.update_ok_button()

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def update_ok_button(self):
        any_checked = any(cb.isChecked() for cb in self.checkboxes)
        self.ok_button.setEnabled(any_checked)
        self.labelWarning.setText("" if any_checked else "No information selected.")

    def on_group_time_toggled(self, checked):
        self.checkMinTime.setEnabled(checked)
        self.checkMaxTime.setEnabled(checked)

        if checked:
            self.checkMinTime.setChecked(True)
            self.checkMaxTime.setChecked(True)
        else:
            self.checkMinTime.setChecked(False)
            self.checkMaxTime.setChecked(False)

        self.update_ok_button()

    def on_group_intensity_toggled(self, checked):
        self.checkMinIntensity.setEnabled(checked)
        self.checkMaxIntensity.setEnabled(checked)

        if checked:
            self.checkMinIntensity.setChecked(True)
            self.checkMaxIntensity.setChecked(True)
        else:
            self.checkMinIntensity.setChecked(False)
            self.checkMaxIntensity.setChecked(False)

        self.update_ok_button()

    def on_group_spatial_toggled(self, checked):
        self.checkNumPoints.setEnabled(checked)
        self.checkArea.setEnabled(checked)
        self.checkDensity.setEnabled(checked)
        self.checkBounds.setEnabled(checked)
        self.checkXAxisBounds.setEnabled(checked)
        self.checkYAxisBounds.setEnabled(checked)

        if checked:
            self.checkNumPoints.setChecked(True)
            self.checkArea.setChecked(True)
            self.checkDensity.setChecked(True)
            self.checkBounds.setChecked(True)
            self.checkXAxisBounds.setChecked(True)
            self.checkYAxisBounds.setChecked(True)
        else:
            self.checkNumPoints.setChecked(False)
            self.checkArea.setChecked(False)
            self.checkDensity.setChecked(False)
            self.checkBounds.setChecked(False)
            self.checkXAxisBounds.setChecked(False)
            self.checkYAxisBounds.setChecked(False)

        self.update_ok_button()

    def on_group_file_metadata_toggled(self, checked):
        self.checkFileName.setEnabled(checked)
        self.checkFileSource.setEnabled(checked)
        self.checkGlobalEncoding.setEnabled(checked)
        self.checkSystemId.setEnabled(checked)
        self.checkGenSoftware.setEnabled(checked)
        self.checkVersion.setEnabled(checked)
        self.checkPointFormat.setEnabled(checked)
        self.checkCreationDate.setEnabled(checked)

        if checked:
            self.checkFileName.setChecked(True)
            self.checkFileSource.setChecked(True)
            self.checkGlobalEncoding.setChecked(True)
            self.checkSystemId.setChecked(True)
            self.checkGenSoftware.setChecked(True)
            self.checkVersion.setChecked(True)
            self.checkPointFormat.setChecked(True)
            self.checkCreationDate.setChecked(True)
        else:
            self.checkFileName.setChecked(False)
            self.checkFileSource.setChecked(False)
            self.checkGlobalEncoding.setChecked(False)
            self.checkSystemId.setChecked(False)
            self.checkGenSoftware.setChecked(False)
            self.checkVersion.setChecked(False)
            self.checkPointFormat.setChecked(False)
            self.checkCreationDate.setChecked(False)

        self.update_ok_button()

    def on_group_classification_toggled(self, checked):
        self.checkClassCounts.setEnabled(checked)
        self.checkReturnCounts.setEnabled(checked)

        if checked:
            self.checkClassCounts.setChecked(True)
            self.checkReturnCounts.setChecked(True)
        else:
            self.checkClassCounts.setChecked(False)
            self.checkReturnCounts.setChecked(False)

        self.update_ok_button()
