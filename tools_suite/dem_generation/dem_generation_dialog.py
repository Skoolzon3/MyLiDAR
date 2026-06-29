# --- General imports ---
import os

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,QDialogButtonBox, QFileDialog, QLineEdit, QSizePolicy, QTextBrowser, QWidget, QSpacerItem, QGroupBox, QFormLayout, QDoubleSpinBox, QCheckBox
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsPointCloudLayer

# --- Log management imports ---
from ..utils import select_log_file, default_suffix_path

# -----------------------------------
# --- DEM Generation Dialog Class ---
# -----------------------------------

class DemGenerationDialog(QDialog):
    def __init__(self, parent=None, tr=lambda s: s):
        super().__init__(parent)
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        
        self.tr = tr
        self.selected_input = None
        self.selected_output = None
        self.is_layer = False
        self.user_edited_output = False

        # --- Window ---
        self.setWindowTitle(self.tr("Generate Bare Earth DEM"))
        self.resize(930, 440)
        self.setMinimumWidth(820)

        # --- Layout ---
        main_layout = QHBoxLayout(self)

        # --- Left Panel (Inputs, Parameters, and Buttons) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Input selection ---
        left_layout.addWidget(QLabel(self.tr("LiDAR layer or file:")))
        input_layout = QHBoxLayout()
        self.input_combo = QComboBox()
        input_layout.addWidget(self.input_combo)
        self.input_button = QPushButton("...")
        self.input_button.setFixedWidth(28)
        input_layout.addWidget(self.input_button)
        left_layout.addLayout(input_layout)

        # --- Output selection ---
        left_layout.addWidget(QLabel(self.tr("Output DEM file:")))
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(self.tr("Select output raster path (.tif)..."))
        output_layout.addWidget(self.output_edit)
        self.output_button = QPushButton("...")
        self.output_button.setToolTip(self.tr("Select output raster file (.tif)"))
        self.output_button.setFixedWidth(28)
        output_layout.addWidget(self.output_button)
        left_layout.addLayout(output_layout)

        # --- DEM parameters group ---
        param_group = QGroupBox(self.tr("DEM Generation Parameters"))
        param_layout = QFormLayout(param_group)

        # Interpolation method
        self.method_combo = QComboBox()
        self.method_combo.addItem(self.tr("Grid-based (min Z per cell)"), False)
        self.method_combo.addItem(self.tr("Triangulation-based (TIN)"), True)
        param_layout.addRow(self.tr("Interpolation method:"), self.method_combo)

        # Cell size
        self.cell_size_label = QLabel(self.tr("Cell size:"))
        self.cell_size_spin = QDoubleSpinBox()
        self.cell_size_spin.setRange(0.1, 1000.0)
        self.cell_size_spin.setSingleStep(0.1)
        self.cell_size_spin.setValue(1.0)
        self.cell_size_spin.setDecimals(2)
        self.cell_size_spin.setSuffix(self.tr(" units"))
        self.cell_size_spin.setToolTip(self.tr("DEM grid cell size. Uses layer CRS units when assigned, or raw coordinate units otherwise."))
        param_layout.addRow(self.cell_size_label, self.cell_size_spin)

        # Hillshade checkbox
        self.hillshade_check = QCheckBox(self.tr("Generate Hillshade"))
        self.hillshade_check.setChecked(True)
        param_layout.addRow("", self.hillshade_check)

        # Hillshade output
        self.hillshade_output_edit = QLineEdit()
        self.hillshade_output_edit.setPlaceholderText(self.tr("Select hillshade output path (.tif)..."))
        self.hillshade_output_button = QPushButton("...")
        self.hillshade_output_button.setToolTip(self.tr("Select hillshade file path (.tif)"))
        self.hillshade_output_button.setFixedWidth(28)
        hillshade_output_layout = QHBoxLayout()
        hillshade_output_layout.addWidget(self.hillshade_output_edit)
        hillshade_output_layout.addWidget(self.hillshade_output_button)
        param_layout.addRow(self.tr("Hillshade output:"), hillshade_output_layout)

        # --- Hillshade parameters ---
        # Z factor
        self.z_factor_spin = QDoubleSpinBox()
        self.z_factor_spin.setRange(0.0, 1000.0)
        self.z_factor_spin.setDecimals(6)
        self.z_factor_spin.setSingleStep(0.1)
        self.z_factor_spin.setValue(1.0)
        self.z_factor_spin.setToolTip(self.tr("Vertical exaggeration multiplier. Use >1 to enhance relief, <1 to reduce. Default=1 (no exaggeration)."))
        param_layout.addRow(self.tr("Z factor:"), self.z_factor_spin)

        # Azimuth
        self.azimuth_spin = QDoubleSpinBox()
        self.azimuth_spin.setRange(0.0, 360.0)
        self.azimuth_spin.setDecimals(6)
        self.azimuth_spin.setSingleStep(1.0)
        self.azimuth_spin.setValue(300.0)
        self.azimuth_spin.setToolTip(self.tr("Sun/light direction in degrees clockwise from North (0°=N, 90°=E, 180°=S, 270°=W). Default=300° (NW lighting)."))
        self.azimuth_spin.setSuffix(self.tr(" °"))
        param_layout.addRow(self.tr("Azimuth:"), self.azimuth_spin)

        # Vertical angle
        self.vertical_angle_spin = QDoubleSpinBox()
        self.vertical_angle_spin.setRange(0.0, 90.0)
        self.vertical_angle_spin.setDecimals(6)
        self.vertical_angle_spin.setSingleStep(1.0)
        self.vertical_angle_spin.setValue(40.0)
        self.vertical_angle_spin.setToolTip(self.tr("Sun elevation above horizon (0°=horizon, 90°=overhead). Lower values create more shadows. Default=40° (midday sun)."))
        self.vertical_angle_spin.setSuffix(self.tr(" °"))
        param_layout.addRow(self.tr("Vertical angle:"), self.vertical_angle_spin)

        self.update_hillshade_output_state(self.hillshade_check.isChecked())
        self.hillshade_check.toggled.connect(self.update_hillshade_output_state)
        self.hillshade_output_button.clicked.connect(self.select_hillshade_output_file)

        left_layout.addWidget(param_group)
        left_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        self.on_method_changed(self.method_combo.currentIndex())

        # --- Log file option ---
        log_layout = QHBoxLayout()
        self.generate_log_checkbox = QCheckBox(self.tr("Generate report log file"))
        log_layout.addWidget(self.generate_log_checkbox)
        log_layout.addStretch()
        left_layout.addLayout(log_layout)

        # --- Log file path ---
        log_path_layout = QHBoxLayout()
        self.log_edit = QLineEdit()
        self.log_edit.setPlaceholderText(self.tr("Default: <output>_outlier_removal_report.txt"))
        self.log_edit.setEnabled(False)
        log_path_layout.addWidget(self.log_edit)
        self.log_button = QPushButton("...")
        self.log_button.setToolTip(self.tr("Select report log file"))
        self.log_button.setFixedWidth(28)
        self.log_button.setEnabled(False)
        log_path_layout.addWidget(self.log_button)
        left_layout.addLayout(log_path_layout)

        # --- OK / Cancel buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        left_layout.addWidget(buttons)

        # --- Right Panel (Description) ---
        desc_box = QTextBrowser()
        desc_box.setFixedWidth(320)
        desc_box.setOpenExternalLinks(False)
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

        title = self.tr("Bare Earth DEM Generation")
        intro = self.tr("This tool generates a Bare Earth DEM by filtering ground-classified points from LiDAR data and interpolating them into a continuous elevation grid.")
        workflow = self.tr("Workflow:")
        step1 = self.tr("Extracts ground-classified points (code 2).")
        step2 = self.tr("Interpolates points into a raster DEM using either TIN or grid-based methods.")
        step3 = self.tr("Optionally generates a hillshade raster for visualization.")
        note = self.tr("The output raster represents the underlying terrain surface without vegetation or buildings.")

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
        self.generate_log_checkbox.stateChanged.connect(self.on_log_changed)
        self.log_button.clicked.connect(self.select_log_file)
        self.output_edit.textChanged.connect(self.update_default_log_path)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    # --- Layer & File Management ---
    def populate_input_layers(self):
        """Populate combo with available LiDAR point cloud layers."""
        self.input_combo.clear()
        layers = [
            layer for layer in QgsProject.instance().mapLayers().values()
            if isinstance(layer, QgsPointCloudLayer)
        ]
        if not layers:
            return
        for layer in layers:
            crs = f" [{layer.crs().authid()}]" if layer.crs().isValid() else ""
            self.input_combo.addItem(f"{layer.name()}{crs}", layer)
        self.input_combo.setCurrentIndex(0)
        self.on_input_changed(0)

    def on_input_changed(self, index):
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
        """Suggest a default DEM and hillshade output filename."""
        if not self.selected_input:
            return

        base_name = os.path.splitext(os.path.basename(self.selected_input))[0]
        base_dir = os.path.dirname(self.selected_input)

        # Interpolation method
        use_triangulation = self.method_combo.currentData()
        method_suffix = "_TIN" if use_triangulation else "_cell"

        # DEM output
        default_dem = os.path.join(base_dir, f"{base_name}_bare_earth_dem{method_suffix}.tif")
        self.output_edit.setText(default_dem)
        self.selected_output = default_dem

        # Hillshade output
        default_hillshade = os.path.join(base_dir, f"{base_name}_bare_earth_hillshade{method_suffix}.tif")
        self.hillshade_output_edit.setText(default_hillshade)

    def select_input_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select LiDAR File"), "", self.tr("LiDAR Files (*.las *.laz)")
        )
        if filename:
            self.input_combo.addItem(filename, filename)
            self.input_combo.setCurrentIndex(self.input_combo.count() - 1)
            self.selected_input = filename
            self.is_layer = False
            self.user_edited_output = False
            self.update_default_output()

    def select_output_file(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Bare Earth DEM"),
            self.output_edit.text() or "",
            self.tr("GeoTIFF (*.tif)")
        )
        if filename:
            self.output_edit.setText(filename)
            self.selected_output = filename
            self.user_edited_output = True

    def get_values(self):
        """Return (cell_size, use_triangulation, hillshade_requested)."""
        cell_size = self.cell_size_spin.value()
        use_triangulation = self.method_combo.currentData()
        hillshade_requested = self.hillshade_check.isChecked()
        hillshade_output = self.hillshade_output_edit.text().strip() if hillshade_requested else ""
        z_factor = self.z_factor_spin.value()
        azimuth = self.azimuth_spin.value()
        vertical_angle = self.vertical_angle_spin.value()

        return (cell_size, use_triangulation, hillshade_requested, hillshade_output, z_factor, azimuth, vertical_angle)

    def get_input_output(self):
        """Return (input_path, output_path)."""
        return self.selected_input, self.output_edit.text().strip()

    def update_hillshade_output_state(self, checked):
        self.hillshade_output_edit.setEnabled(checked)
        self.hillshade_output_button.setEnabled(checked)
        self.z_factor_spin.setEnabled(checked)
        self.azimuth_spin.setEnabled(checked)
        self.vertical_angle_spin.setEnabled(checked)

    def select_hillshade_output_file(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Hillshade"),
            self.hillshade_output_edit.text() or "",
            self.tr("GeoTIFF (*.tif)")
        )
        if filename:
            self.hillshade_output_edit.setText(filename)

    def on_method_changed(self, index):
        """Show/hide cell size and update default output names."""
        use_triangulation = self.method_combo.itemData(index)
        is_cell_based = not bool(use_triangulation)
        self.cell_size_label.setVisible(is_cell_based)
        self.cell_size_spin.setVisible(is_cell_based)

        if not self.user_edited_output:
            self.update_default_output()

    # --- Log File Management ---

    def get_log_path(self):
        if not self.generate_log_checkbox.isChecked():
            return None

        log_text = self.log_edit.text().strip()
        if log_text:
            return log_text

        output_path = self.output_edit.text().strip()
        return default_suffix_path(output_path, "_dem_generation_report", ".txt")

    def update_default_log_path(self):
        if not self.generate_log_checkbox.isChecked():
            return

        output_path = self.output_edit.text().strip()
        default_log = default_suffix_path(output_path, "_dem_generation_report", ".txt")
        if not default_log:
            return

        if not hasattr(self, 'selected_log') or not self.selected_log:
            self.log_edit.setText(default_log)

    def on_log_changed(self, state):
        enabled = state == Qt.CheckState.Checked
        self.log_edit.setEnabled(enabled)
        self.log_button.setEnabled(enabled)

        if enabled:
            self.update_default_log_path()
        else:
            self.selected_log = None
            pass

    def select_log_file(self):
        initial_path = self.log_edit.text().strip()
        if not initial_path:
            output_path = self.output_edit.text().strip()
            initial_path = default_suffix_path(output_path, "_dem_generation_report", ".txt") or ""

        filename = select_log_file(self,self.tr("Save Report Log"),self.tr,initial_path)
        if filename:
            self.log_edit.setText(filename)
            self.selected_log = filename
