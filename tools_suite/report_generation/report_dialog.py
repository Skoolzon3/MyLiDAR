# -----------------------
# --- UI Dialog Class ---
# -----------------------

import os
from qgis.PyQt.QtWidgets import QDialogButtonBox, QDialog
from qgis.PyQt import uic

form_class, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "./report_form.ui"))

class ReportDialog(QDialog, form_class):
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.setupUi(self)
        self.tr = translator if translator else (lambda s: s)

        # === Window and main labels ===
        self.setWindowTitle(self.tr("Select Report Contents"))
        self.label.setText(self.tr("Select the information to include in the report:"))
        self.labelWarning.setText(self.tr("No information selected"))

        # === Groups ===
        self.groupFileMetadata.setTitle(self.tr("File Metadata"))
        self.groupSpatial.setTitle(self.tr("Spatial"))
        self.groupIntensity.setTitle(self.tr("Intensity"))
        self.groupTime.setTitle(self.tr("Time"))
        self.groupClassification.setTitle(self.tr("Classification"))
        self.groupOutputFormat.setTitle(self.tr("Output Format"))

        # === Metadata checkboxes ===
        self.checkFileName.setText(self.tr("File Name"))
        self.checkFileName.setToolTip(self.tr("File name of the LiDAR dataset"))

        self.checkFileSource.setText(self.tr("File Source"))
        self.checkFileSource.setToolTip(self.tr("Source ID specified in the LAS file header, identifying the generating system"))

        self.checkGlobalEncoding.setText(self.tr("Global Encoding"))
        self.checkGlobalEncoding.setToolTip(self.tr("Flags describing GPS time type, waveform data and other global settings"))

        self.checkSystemId.setText(self.tr("System ID"))
        self.checkSystemId.setToolTip(self.tr("Identifier of the system that created the file"))

        self.checkGenSoftware.setText(self.tr("Generating Software"))
        self.checkGenSoftware.setToolTip(self.tr("Name of the software that generated the LAS file"))

        self.checkVersion.setText(self.tr("LAS Version"))
        self.checkVersion.setToolTip(self.tr("LAS file format version (e.g., 1.2, 1.4)"))

        self.checkPointFormat.setText(self.tr("Point Format"))
        self.checkPointFormat.setToolTip(self.tr("Point data record format used in the LAS file (e.g., Format 0, 1, 6) and its corresponding byte size"))

        self.checkCreationDate.setText(self.tr("Creation Date"))
        self.checkCreationDate.setToolTip(self.tr("Date the LAS file was created, extracted from the file's header"))

        # === Intensity checkboxes ===
        self.checkMinIntensity.setText(self.tr("Min Intensity"))
        self.checkMinIntensity.setToolTip(self.tr("Lowest recorded intensity value in the dataset"))

        self.checkMaxIntensity.setText(self.tr("Max Intensity"))
        self.checkMaxIntensity.setToolTip(self.tr("Highest recorded intensity value in the dataset"))

        # === Spatial checkboxes ===
        self.checkNumPoints.setText(self.tr("Number of Points"))
        self.checkNumPoints.setToolTip(self.tr("Total number of points in the dataset"))

        self.checkArea.setText(self.tr("Area"))
        self.checkArea.setToolTip(self.tr("Area covered by the point cloud, based on spatial extent"))

        self.checkDensity.setText(self.tr("Density"))
        self.checkDensity.setToolTip(self.tr("Average number of points per unit area (e.g., points per square meter)"))

        self.checkBounds.setText(self.tr("Bounds (Min/Max)"))
        self.checkBounds.setToolTip(self.tr("Minimum and maximum coordinates (X, Y, Z) bounding the dataset"))

        self.checkXAxisBounds.setText(self.tr("X-Axis Bounds"))
        self.checkXAxisBounds.setToolTip(self.tr("Minimum and maximum X-axis values in the dataset"))

        self.checkYAxisBounds.setText(self.tr("Y-Axis Bounds"))
        self.checkYAxisBounds.setToolTip(self.tr("Minimum and maximum Y-axis values in the dataset"))

        self.checkZAxisBounds.setText(self.tr("Z-Axis Bounds"))
        self.checkZAxisBounds.setToolTip(self.tr("Minimum and maximum Z-axis values in the dataset"))

        # === Time checkboxes ===
        self.checkMinTime.setText(self.tr("Min Time"))
        self.checkMinTime.setToolTip(self.tr("Earliest timestamp recorded in the dataset"))

        self.checkMaxTime.setText(self.tr("Max Time"))
        self.checkMaxTime.setToolTip(self.tr("Latest timestamp recorded in the dataset"))

        # === Classification checkboxes ===
        self.checkClassCounts.setText(self.tr("Class Counts"))
        self.checkClassCounts.setToolTip(self.tr("Counts of points by classification codes (e.g., ground, vegetation, building...)"))

        # === Return counts checkbox ===
        self.checkReturnCounts.setText(self.tr("Return Counts"))
        self.checkReturnCounts.setToolTip(self.tr("Counts of points by return number (first, last...)"))

        # === Dock option ===
        self.checkGenerateDock.setText(self.tr("Generate Dock Panel in QGIS"))
        self.checkGenerateDock.setToolTip(self.tr("If checked, a dockable report panel will be created alongside the generated report in QGIS"))

        # === Buttons ===
        self.btnSelectAll.setText(self.tr("Select All Attributes"))

        # === Output Format checkboxes (formerly radio buttons) ===
        self.checkTxt.setText(self.tr("Plain Text (.txt)"))
        self.checkMarkdown.setText("Markdown (.md)")
        self.checkPdf.setText("PDF (.pdf)")
        self.checkGenerateDock.setText(self.tr("Generate Dock Panel in QGIS"))
        self.checkGenerateDock.setToolTip(self.tr("If checked, a dockable report panel will be created alongside the generated report in QGIS"))

        # === Toggle groups and connect signals ===
        self.groupTime.toggled.connect(self.on_group_time_toggled)
        self.groupIntensity.toggled.connect(self.on_group_intensity_toggled)
        self.groupSpatial.toggled.connect(self.on_group_spatial_toggled)
        self.groupFileMetadata.toggled.connect(self.on_group_file_metadata_toggled)
        self.groupClassification.toggled.connect(self.on_group_classification_toggled)

        self.btnSelectAll.clicked.connect(self.on_select_all_clicked)

        self.checkTxt.stateChanged.connect(self.validate_state)
        self.checkMarkdown.stateChanged.connect(self.validate_state)
        self.checkPdf.stateChanged.connect(self.validate_state)

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
            self.checkZAxisBounds,

            # GPS time checkboxes
            self.checkMinTime,
            self.checkMaxTime,

            # Point metrics checkboxes
            self.checkClassCounts,
            self.checkReturnCounts,
        ]

        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        for checkbox in self.checkboxes:
            checkbox.stateChanged.connect(self.validate_state)

        self.validate_state()

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def on_group_time_toggled(self, checked):
        self.checkMinTime.setEnabled(checked)
        self.checkMaxTime.setEnabled(checked)

        if checked:
            self.checkMinTime.setChecked(True)
            self.checkMaxTime.setChecked(True)
        else:
            self.checkMinTime.setChecked(False)
            self.checkMaxTime.setChecked(False)

        self.validate_state()

    def on_group_intensity_toggled(self, checked):
        self.checkMinIntensity.setEnabled(checked)
        self.checkMaxIntensity.setEnabled(checked)

        if checked:
            self.checkMinIntensity.setChecked(True)
            self.checkMaxIntensity.setChecked(True)
        else:
            self.checkMinIntensity.setChecked(False)
            self.checkMaxIntensity.setChecked(False)

        self.validate_state()

    def on_group_spatial_toggled(self, checked):
        self.checkNumPoints.setEnabled(checked)
        self.checkArea.setEnabled(checked)
        self.checkDensity.setEnabled(checked)
        self.checkBounds.setEnabled(checked)
        self.checkXAxisBounds.setEnabled(checked)
        self.checkYAxisBounds.setEnabled(checked)
        self.checkZAxisBounds.setEnabled(checked)

        if checked:
            self.checkNumPoints.setChecked(True)
            self.checkArea.setChecked(True)
            self.checkDensity.setChecked(True)
            self.checkBounds.setChecked(True)
            self.checkXAxisBounds.setChecked(True)
            self.checkYAxisBounds.setChecked(True)
            self.checkZAxisBounds.setChecked(True)
        else:
            self.checkNumPoints.setChecked(False)
            self.checkArea.setChecked(False)
            self.checkDensity.setChecked(False)
            self.checkBounds.setChecked(False)
            self.checkXAxisBounds.setChecked(False)
            self.checkYAxisBounds.setChecked(False)
            self.checkZAxisBounds.setChecked(False)

        self.validate_state()

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

        self.validate_state()

    def on_group_classification_toggled(self, checked):
        self.checkClassCounts.setEnabled(checked)
        self.checkReturnCounts.setEnabled(checked)

        if checked:
            self.checkClassCounts.setChecked(True)
            self.checkReturnCounts.setChecked(True)
        else:
            self.checkClassCounts.setChecked(False)
            self.checkReturnCounts.setChecked(False)

        self.validate_state()

    def on_select_all_clicked(self):
        for cb in self.checkboxes:
            cb.setEnabled(True)
            cb.setChecked(True)

        self.groupFileMetadata.setChecked(True)
        self.groupSpatial.setChecked(True)
        self.groupIntensity.setChecked(True)
        self.groupTime.setChecked(True)
        self.groupClassification.setChecked(True)

        self.validate_state()

    def selected_formats(self):
        formats = []
        if self.checkTxt.isChecked():
            formats.append("txt")
        if self.checkMarkdown.isChecked():
            formats.append("md")
        if self.checkPdf.isChecked():
            formats.append("pdf")
        return formats

    def generate_dock(self):
        return self.checkGenerateDock.isChecked()

    def validate_state(self):
        any_info_checked = any(cb.isChecked() for cb in self.checkboxes)
        any_format_checked = (
            self.checkTxt.isChecked() or
            self.checkMarkdown.isChecked() or
            self.checkPdf.isChecked()
        )

        self.labelWarning.setVisible(not any_info_checked)
        self.labelWarning.setText("" if any_info_checked else self.tr("No information selected"))

        self.labelWarningOutputFormat.setVisible(not any_format_checked)
        self.labelWarningOutputFormat.setText("" if any_format_checked else self.tr("No output format selected"))

        self.ok_button.setEnabled(any_info_checked and any_format_checked)
