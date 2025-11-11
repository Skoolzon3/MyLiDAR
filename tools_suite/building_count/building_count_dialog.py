from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,QDialogButtonBox, QFileDialog, QLineEdit, QSizePolicy, QTextBrowser, QWidget, QSpacerItem, QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsPointCloudLayer
import os

class BuildingCountDialog(QDialog):
    def __init__(self, parent=None, tr=lambda s: s):
        super().__init__(parent)
        self.tr = tr
        self.selected_input = None
        self.selected_output = None
        self.is_layer = False
        self.user_edited_output = False

        # --- Window ---
        self.setWindowTitle(tr("Count Buildings"))
        self.resize(900, 370)
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
        left_layout.addWidget(QLabel(tr("LiDAR layer or file:")))
        input_layout = QHBoxLayout()

        self.input_combo = QComboBox()
        input_layout.addWidget(self.input_combo)

        self.input_button = QPushButton("...")
        self.input_button.setToolTip(tr("Select input LiDAR file (.las / .laz)"))
        self.input_button.setFixedWidth(28)
        input_layout.addWidget(self.input_button)

        left_layout.addLayout(input_layout)

        # --- Output selection ---
        left_layout.addWidget(QLabel(tr("Output vector file (optional):")))
        output_layout = QHBoxLayout()

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(tr("Select output file path (optional)..."))
        output_layout.addWidget(self.output_edit)

        self.output_button = QPushButton("...")
        self.output_button.setToolTip(tr("Select output file (.gpkg / .shp)"))
        self.output_button.setFixedWidth(28)
        output_layout.addWidget(self.output_button)

        left_layout.addLayout(output_layout)

        # --- Clustering parameters group ---
        param_group = QGroupBox(tr("DBSCAN Parameters"))
        param_layout = QFormLayout(param_group)
        param_layout.setLabelAlignment(Qt.AlignLeft)
        param_layout.setFormAlignment(Qt.AlignTop)

        # Radio de búsqueda
        self.eps_spin = QDoubleSpinBox()
        self.eps_spin.setRange(0.1, 100.0)
        self.eps_spin.setSingleStep(0.1)
        self.eps_spin.setValue(2.0)
        self.eps_spin.setSuffix(" m")
        param_layout.addRow(tr("Search radius:"), self.eps_spin)

        # Min samples
        self.min_samples_spin = QSpinBox()
        self.min_samples_spin.setRange(1, 1000)
        self.min_samples_spin.setValue(30)
        param_layout.addRow(tr("Min samples:"), self.min_samples_spin)

        # Z-axis (3D clustering)
        self.use_z_check = QCheckBox(tr("Use Z-axis (3D clustering)"))
        self.use_z_check.setChecked(True)
        param_layout.addRow("", self.use_z_check)

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

        title = self.tr("Building Count (DBSCAN)")
        intro = self.tr("This tool estimates the number of buildings in a LiDAR dataset by clustering points classified as buildings (code 6).")
        workflow = self.tr("Workflow:")
        step1 = self.tr("Filters building-classified points (code 6).")
        step2 = self.tr("Applies DBSCAN clustering to group nearby building points.")
        step3 = self.tr("Creates polygons representing each detected building cluster.")
        note = self.tr("The number of detected clusters approximates the total number of buildings.")

        desc_box.setHtml(f"""
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
        """)

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
        """Populate combo with available LiDAR layers."""
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
        """Propose a default output name."""
        if not self.selected_input:
            return
        base_name = os.path.splitext(os.path.basename(self.selected_input))[0]
        default_output = os.path.join(
            os.path.dirname(self.selected_input),
            base_name + "_detected_buildings.gpkg"
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
            self, self.tr("Select Output File"),
            self.output_edit.text() or "",
            self.tr("GeoPackage (*.gpkg);;Shapefile (*.shp)")
        )
        if filename:
            self.output_edit.setText(filename)
            self.selected_output = filename
            self.user_edited_output = True

    # --- Accessors ---
    def get_params(self):
        """Return eps, min_samples, use_z."""
        return (
            self.eps_spin.value(),
            self.min_samples_spin.value(),
            self.use_z_check.isChecked()
        )

    def get_input_output(self):
        """Return (input_path, output_path)."""
        return self.selected_input, self.output_edit.text().strip()
