from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,QDialogButtonBox, QFileDialog, QLineEdit, QSizePolicy, QTextBrowser, QWidget, QSpacerItem, QGroupBox, QFormLayout, QDoubleSpinBox, QCheckBox
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsPointCloudLayer
import os

class DemGenerationDialog(QDialog):
    def __init__(self, parent=None, translator=lambda s: s):
        super().__init__(parent)
        self.tr = translator
        self.selected_input = None
        self.selected_output = None
        self.is_layer = False
        self.user_edited_output = False

        # --- Window ---
        self.setWindowTitle(self.tr("Generate Bare Earth DEM"))
        self.resize(900, 440)
        self.setMinimumWidth(820)

        # --- Layout ---
        main_layout = QHBoxLayout(self)

        # --- Left Panel (Inputs, Parameters, and Buttons) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.setAlignment(Qt.AlignTop)

        # --- Input selection ---
        left_layout.addWidget(QLabel(self.tr("LiDAR layer or file:")))
        input_layout = QHBoxLayout()

        self.input_combo = QComboBox()
        input_layout.addWidget(self.input_combo)

        self.input_button = QPushButton("...")
        self.input_button.setToolTip(self.tr("Select LiDAR file (.las / .laz)"))
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

        # Cell size
        self.cell_size_spin = QDoubleSpinBox()
        self.cell_size_spin.setRange(0.1, 1000.0)
        self.cell_size_spin.setSingleStep(0.1)
        self.cell_size_spin.setValue(1.0)
        self.cell_size_spin.setDecimals(2)
        self.cell_size_spin.setSuffix(" m")
        param_layout.addRow(self.tr("Cell size:"), self.cell_size_spin)

        # Interpolation method
        self.method_combo = QComboBox()
        self.method_combo.addItem(self.tr("Grid-based (min Z per cell)"), False)
        self.method_combo.addItem(self.tr("Triangulation-based (TIN)"), True)
        param_layout.addRow(self.tr("Interpolation method:"), self.method_combo)

        # Hillshade checkbox
        self.hillshade_check = QCheckBox(self.tr("Generate Hillshade"))
        self.hillshade_check.setChecked(True)
        param_layout.addRow("", self.hillshade_check)

        left_layout.addWidget(param_group)
        left_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- OK / Cancel buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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
        """Suggest a default DEM output filename."""
        if not self.selected_input:
            return
        base_name = os.path.splitext(os.path.basename(self.selected_input))[0]
        default_output = os.path.join(
            os.path.dirname(self.selected_input),
            base_name + "_bare_earth_dem.tif"
        )
        self.output_edit.setText(default_output)
        self.selected_output = default_output

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
        return cell_size, use_triangulation, hillshade_requested

    def get_input_output(self):
        """Return (input_path, output_path)."""
        return self.selected_input, self.output_edit.text().strip()
