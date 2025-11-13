import os
from qgis.core import QgsProject, QgsPointCloudLayer
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QCheckBox, QPushButton, QDialogButtonBox, QScrollArea, QWidget, QSpacerItem, QSizePolicy, QLineEdit, QTextBrowser, QFileDialog, QComboBox, QGridLayout
from qgis.PyQt.QtCore import Qt

class ReportGenerationDialog(QDialog):
    """Dialog window for selecting LiDAR report contents and output."""
    def __init__(self, parent=None, tr=lambda s: s):
        super().__init__(parent)
        self.tr = tr
        self.selected_input = None
        self.selected_output = None
        self.is_layer = False
        self.user_edited_output = False

        # --- Window ---
        self.setWindowTitle(tr("Generate LiDAR File Report"))
        self.resize(900, 500)
        self.setMinimumWidth(885)

        # --- Layout ---
        main_layout = QHBoxLayout(self)

        # --- Left Panel (Inputs, Options, Buttons) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.setAlignment(Qt.AlignTop)

        # --- Input selection ---
        left_layout.addWidget(QLabel(tr("LiDAR layer or file:")))
        input_layout = QHBoxLayout()
        self.input_combo = QComboBox()
        self.input_combo.setEditable(False)
        input_layout.addWidget(self.input_combo)

        self.input_button = QPushButton("...")
        self.input_button.setToolTip(tr("Select input file (.las / .laz)"))
        self.input_button.setFixedWidth(28)
        self.input_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        input_layout.addWidget(self.input_button)
        left_layout.addLayout(input_layout)

        # --- Output selection ---
        left_layout.addWidget(QLabel(tr("Output report file:")))
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(tr("Select output report file path..."))
        output_layout.addWidget(self.output_edit)

        self.output_button = QPushButton("...")
        self.output_button.setToolTip(tr("Select output file (.txt / .md / .pdf /.tex)"))
        self.output_button.setFixedWidth(28)
        self.output_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        output_layout.addWidget(self.output_button)
        left_layout.addLayout(output_layout)

        # --- Scroll area for report options ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(scroll_widget)
        left_layout.addWidget(scroll, stretch=1)

        # === Section: Selection Info ===
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignLeft)

        self.label = QLabel(self.tr("Report Attributes"))
        self.label.setStyleSheet("font-weight: 600; font-size: 9pt;")
        header_layout.addWidget(self.label)

        header_layout.addStretch()

        self.btnSelectAll = QPushButton(self.tr("Select All Attributes"))
        self.btnSelectAll.setFixedWidth(150)
        header_layout.addWidget(self.btnSelectAll)

        scroll_layout.addLayout(header_layout)

        self.labelWarning = QLabel(self.tr("No information selected"))
        self.labelWarning.setStyleSheet("color: #d9534f; font-style: italic;")
        scroll_layout.addWidget(self.labelWarning)

        # --- Report Groups ---
        groups_container = QWidget()
        groups_layout = QGridLayout(groups_container)
        groups_layout.setColumnStretch(0, 1)
        groups_layout.setColumnStretch(1, 1)
        groups_layout.setHorizontalSpacing(15)
        groups_layout.setVerticalSpacing(10)

        self.groupFileMetadata = self.create_group(self.tr("File Metadata"), groups_layout)
        self.groupSpatial = self.create_group(self.tr("Spatial"), groups_layout)
        self.groupIntensity = self.create_group(self.tr("Intensity"), groups_layout)
        self.groupTime = self.create_group(self.tr("Time"), groups_layout)
        self.groupClassification = self.create_group(self.tr("Classification"), groups_layout)

        groups_layout.addWidget(self.groupFileMetadata, 0, 0)
        groups_layout.addWidget(self.groupSpatial, 0, 1)
        groups_layout.addWidget(self.groupIntensity, 1, 0)
        groups_layout.addWidget(self.groupTime, 1, 1)
        groups_layout.addWidget(self.groupClassification, 2, 0, 1, 2)  # full width if desired

        scroll_layout.addWidget(groups_container)

        # --- Output Format ---
        self.groupOutputFormat = QGroupBox(self.tr("Output Format"))
        scroll_layout.addWidget(self.groupOutputFormat)
        self.groupOutputFormat.setCheckable(False)
        output_layout_format = QVBoxLayout(self.groupOutputFormat)
        output_layout_format.setAlignment(Qt.AlignTop)

        # === File Metadata ===
        self.checkFileName = self.add_check(self.groupFileMetadata, "File Name", "File name of the LiDAR dataset")
        self.checkFileSource = self.add_check(self.groupFileMetadata, "File Source", "Source ID specified in the LAS file header")
        self.checkGlobalEncoding = self.add_check(self.groupFileMetadata, "Global Encoding", "Flags describing GPS time type, waveform data and other global settings")
        self.checkSystemId = self.add_check(self.groupFileMetadata, "System ID", "Identifier of the system that created the file")
        self.checkGenSoftware = self.add_check(self.groupFileMetadata, "Generating Software", "Software that generated the LAS file")
        self.checkVersion = self.add_check(self.groupFileMetadata, "LAS Version", "LAS file format version (e.g., 1.2, 1.4)")
        self.checkPointFormat = self.add_check(self.groupFileMetadata, "Point Format", "Point data record format and byte size")
        self.checkCreationDate = self.add_check(self.groupFileMetadata, "Creation Date", "Date the LAS file was created")

        # === Spatial ===
        self.checkNumPoints = self.add_check(self.groupSpatial, "Number of Points", "Total number of points")
        self.checkArea = self.add_check(self.groupSpatial, "Area", "Area covered by the point cloud")
        self.checkDensity = self.add_check(self.groupSpatial, "Density", "Average number of points per m²")
        self.checkBounds = self.add_check(self.groupSpatial, "Bounds (Min/Max)", "Minimum and maximum X/Y/Z coordinates")
        self.checkXAxisBounds = self.add_check(self.groupSpatial, "X-Axis Bounds")
        self.checkYAxisBounds = self.add_check(self.groupSpatial, "Y-Axis Bounds")
        self.checkZAxisBounds = self.add_check(self.groupSpatial, "Z-Axis Bounds")

        # === Intensity ===
        self.checkMinIntensity = self.add_check(self.groupIntensity, "Min Intensity")
        self.checkMaxIntensity = self.add_check(self.groupIntensity, "Max Intensity")
        self.checkIntensityMean = self.add_check(self.groupIntensity, "Mean Intensity")
        self.checkIntensitySD = self.add_check(self.groupIntensity, "Standard deviation")

        # === Time ===
        self.checkMinTime = self.add_check(self.groupTime, "Min Time")
        self.checkMaxTime = self.add_check(self.groupTime, "Max Time")

        # === Classification ===
        self.checkClassCounts = self.add_check(self.groupClassification, "Class Counts")
        self.checkReturnCounts = self.add_check(self.groupClassification, "Return Counts")

        # === Output Format ===
        self.checkTxt = self.add_check(self.groupOutputFormat, "Plain Text (.txt)")
        self.checkMarkdown = self.add_check(self.groupOutputFormat, "Markdown (.md)")
        self.checkPdf = self.add_check(self.groupOutputFormat, "PDF (.pdf)")
        self.checkTeX = self.add_check(self.groupOutputFormat, "TeX (.tex)")
        self.checkGenerateDock = self.add_check(self.groupOutputFormat, "Generate Dock Panel in QGIS")

        self.labelWarningOutputFormat = QLabel(self.tr("No output format selected"))
        self.labelWarningOutputFormat.setStyleSheet("color: #d9534f; font-style: italic;")
        scroll_layout.addWidget(self.labelWarningOutputFormat)

        # Default Selections
        self.checkFileName.setChecked(True)
        self.checkVersion.setChecked(True)
        self.checkPointFormat.setChecked(True)
        self.checkNumPoints.setChecked(True)
        self.checkBounds.setChecked(True)
        self.checkTxt.setChecked(True)

        # Default group state
        self.groupFileMetadata.setChecked(True)
        self.groupSpatial.setChecked(True)
        self.groupIntensity.setChecked(True)
        self.groupTime.setChecked(True)
        self.groupClassification.setChecked(False)

        # --- Spacer before buttons ---
        scroll_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- OK/Cancel buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        left_layout.addWidget(buttons)
        self.ok_button = buttons.button(QDialogButtonBox.Ok)

        # --- Right Panel (Description) ---
        desc_box = QTextBrowser()
        desc_box.setOpenExternalLinks(False)
        desc_box.setFixedWidth(320)
        desc_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        desc_box.setStyleSheet("""
            QTextBrowser {
                background-color: #fafafa;
                border: 1px solid #dcdcdc;
                padding: 10px;
                border-radius: 6px;
                font-family: "Segoe UI", sans-serif;
                font-size: 10pt;
            }
        """)

        title = self.tr("LiDAR Report Generator")
        intro = self.tr(
            "This tool creates summary reports for LiDAR datasets, providing metadata, spatial statistics, "
            "intensity measures, classification summaries, and other relevant information."
        )
        workflow = self.tr("Workflow:")
        step1 = self.tr("Select a LiDAR layer or file (.las / .laz).")
        step2 = self.tr("Choose which attributes and metrics to include in the report.")
        step3 = self.tr("Select one or more output formats (TXT, Markdown, PDF, TeX).")
        step4 = self.tr("Optionally generate a dockable report panel in QGIS.")
        note = self.tr("Use this tool to quickly inspect, summarize, or document LiDAR dataset properties.")

        desc_html = f"""
            <div style="position: relative;">
                <h3 style="margin-bottom:4px;">{title}</h3>
                <p style="font-size:9.5pt; color:#444;">{intro}</p>
                <hr style="border:none; border-top:1px solid #ccc; margin:6px 0;">
                <h4 style="margin-bottom:2px;">{workflow}</h4>
                <ul>
                    <li>{step1}</li>
                    <li>{step2}</li>
                    <li>{step3}</li>
                    <li>{step4}</li>
                </ul>
                <p style="margin-top:4px; font-size:9pt; color:#666;">{note}</p>
            </div>
        """
        desc_box.setHtml(desc_html)

        main_layout.addWidget(left_panel, stretch=3)
        main_layout.addWidget(desc_box, stretch=2)

        # --- Connections ---
        self.populate_input_layers()
        self.input_combo.currentIndexChanged.connect(self.on_input_changed)
        self.input_button.clicked.connect(self.select_input_file)
        self.output_button.clicked.connect(self.select_output_file)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # Group toggles
        self.groupFileMetadata.toggled.connect(self.on_group_file_metadata_toggled)
        self.groupSpatial.toggled.connect(self.on_group_spatial_toggled)
        self.groupIntensity.toggled.connect(self.on_group_intensity_toggled)
        self.groupTime.toggled.connect(self.on_group_time_toggled)
        self.groupClassification.toggled.connect(self.on_group_classification_toggled)
        self.btnSelectAll.clicked.connect(self.on_select_all_clicked)

        # Checkbox tracking
        self.checkboxes = [
            self.checkFileName, self.checkFileSource, self.checkGlobalEncoding, self.checkSystemId,
            self.checkGenSoftware, self.checkVersion, self.checkPointFormat, self.checkCreationDate,
            self.checkNumPoints, self.checkArea, self.checkDensity, self.checkBounds,
            self.checkXAxisBounds, self.checkYAxisBounds, self.checkZAxisBounds,
            self.checkMinIntensity, self.checkMaxIntensity, self.checkIntensityMean, self.checkIntensitySD,
            self.checkMinTime, self.checkMaxTime,
            self.checkClassCounts, self.checkReturnCounts
        ]

        for cb in self.checkboxes + [self.checkTxt, self.checkMarkdown, self.checkPdf, self.checkTeX, self.checkGenerateDock]:
            cb.stateChanged.connect(self.validate_state)

        for cb in [self.checkTxt, self.checkMarkdown, self.checkPdf, self.checkTeX]:
            cb.stateChanged.connect(self.on_format_changed)

        self.validate_state()

    # --- Helper Methods ---
    def create_group(self, title, parent_layout):
        group = QGroupBox(self.tr(title))
        group.setCheckable(True)
        group.setChecked(False)
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignTop)
        parent_layout.addWidget(group)
        return group

    def add_check(self, parent_group, text, tooltip=None):
        cb = QCheckBox(self.tr(text))
        if tooltip:
            cb.setToolTip(self.tr(tooltip))
        parent_group.layout().addWidget(cb)
        return cb

    def on_format_changed(self):
        self.validate_state()
        self.update_output_extension()

    # --- Layer & File Management ---
    def populate_input_layers(self):
        """Populate combo with loaded LiDAR layers."""
        self.input_combo.clear()
        layers = [
            lyr for lyr in QgsProject.instance().mapLayers().values()
            if isinstance(lyr, QgsPointCloudLayer)
        ]
        if not layers:
            self.selected_input = None
            self.is_layer = False
            return
        for lyr in layers:
            crs = f" [{lyr.crs().authid()}]" if lyr.crs().isValid() else ""
            self.input_combo.addItem(f"{lyr.name()}{crs}", lyr)
        self.input_combo.setCurrentIndex(0)
        self.on_input_changed(0)

    def on_input_changed(self, index):
        """Update input and output defaults."""
        layer = self.input_combo.itemData(index)
        if isinstance(layer, QgsPointCloudLayer):
            self.selected_input = layer.source()
            self.is_layer = True
        elif isinstance(layer, str):
            self.selected_input = layer
            self.is_layer = False
        else:
            return
        if not self.user_edited_output:
            self.update_default_output()

    def update_default_output(self):
        if not self.selected_input:
            return
        base = os.path.splitext(os.path.basename(self.selected_input))[0]
        default_output = os.path.join(os.path.dirname(self.selected_input), base + "_report.txt")
        self.output_edit.setText(default_output)
        self.selected_output = default_output

    def select_input_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select LiDAR File"), "", self.tr("LiDAR Files (*.las *.laz)")
        )
        if not filename:
            return
        existing_index = self.input_combo.findData(filename)
        if existing_index == -1:
            self.input_combo.addItem(filename, filename)
            self.input_combo.setCurrentIndex(self.input_combo.count() - 1)
        else:
            self.input_combo.setCurrentIndex(existing_index)
        self.selected_input = filename
        self.is_layer = False
        self.user_edited_output = False
        self.update_default_output()

    def select_output_file(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save LiDAR Report File"),
            self.output_edit.text() or "",
            self.tr("Report Files (*.txt *.md *.pdf *.tex)")
        )
        if filename:
            self.output_edit.setText(filename)
            self.selected_output = filename
            self.user_edited_output = True

    def get_input_output(self):
        return self.selected_input, self.output_edit.text().strip()

    # --- Group Logic & Validation ---
    def on_group_time_toggled(self, checked):
        for cb in [self.checkMinTime, self.checkMaxTime]:
            cb.setEnabled(checked)
            cb.setChecked(checked)
        self.validate_state()

    def on_group_intensity_toggled(self, checked):
        for cb in [self.checkMinIntensity, self.checkMaxIntensity, self.checkIntensityMean, self.checkIntensitySD]:
            cb.setEnabled(checked)
            cb.setChecked(checked)
        self.validate_state()

    def on_group_spatial_toggled(self, checked):
        for cb in [self.checkNumPoints, self.checkArea, self.checkDensity,
                   self.checkBounds, self.checkXAxisBounds, self.checkYAxisBounds, self.checkZAxisBounds]:
            cb.setEnabled(checked)
            cb.setChecked(checked)
        self.validate_state()

    def on_group_file_metadata_toggled(self, checked):
        for cb in [self.checkFileName, self.checkFileSource, self.checkGlobalEncoding, self.checkSystemId,
                   self.checkGenSoftware, self.checkVersion, self.checkPointFormat, self.checkCreationDate]:
            cb.setEnabled(checked)
            cb.setChecked(checked)
        self.validate_state()

    def on_group_classification_toggled(self, checked):
        for cb in [self.checkClassCounts, self.checkReturnCounts]:
            cb.setEnabled(checked)
            cb.setChecked(checked)
        self.validate_state()

    def on_select_all_clicked(self):
        for cb in self.checkboxes:
            cb.setEnabled(True)
            cb.setChecked(True)
        for grp in [self.groupFileMetadata, self.groupSpatial, self.groupIntensity,
                    self.groupTime, self.groupClassification]:
            grp.setChecked(True)
        self.validate_state()

    def update_output_extension(self):
        """Update output file extension based on selected output formats."""
        if self.user_edited_output:
            return

        formats = self.selected_formats()
        if not formats:
            return

        current_output = self.output_edit.text().strip()
        if not current_output:
            self.update_default_output()
            current_output = self.output_edit.text().strip()

        base, _ = os.path.splitext(current_output)

        if len(formats) == 1:
            new_ext = f".{formats[0]}"
        else:
            new_ext = ".zip"

        new_output = base + new_ext
        self.output_edit.setText(new_output)
        self.selected_output = new_output

    def validate_state(self):
        any_info = any(cb.isChecked() for cb in self.checkboxes)
        any_format = any(cb.isChecked() for cb in [self.checkTxt, self.checkMarkdown, self.checkPdf, self.checkTeX, self.checkGenerateDock])
        self.labelWarning.setVisible(not any_info)
        self.labelWarningOutputFormat.setVisible(not any_format)
        self.ok_button.setEnabled(any_info and any_format)

    # --- Output Utilities ---
    def selected_formats(self):
        fmt = []
        if self.checkTxt.isChecked():
            fmt.append("txt")
        if self.checkMarkdown.isChecked():
            fmt.append("md")
        if self.checkPdf.isChecked():
            fmt.append("pdf")
        if self.checkTeX.isChecked():
            fmt.append("tex")
        return fmt

    def generate_dock(self):
        return self.checkGenerateDock.isChecked()
