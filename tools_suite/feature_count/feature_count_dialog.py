# --- General imports ---
import os

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,QDialogButtonBox, QFileDialog, QLineEdit, QSizePolicy, QTextBrowser, QWidget, QSpacerItem, QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsPointCloudLayer

# -----------------------------------
# --- Feature Count Dialog Class ---
# -----------------------------------

class FeatureCountDialog(QDialog):
    def __init__(self, parent=None, tr=lambda s: s):
        super().__init__(parent)

        self.tr = tr
        self.selected_input = None
        self.is_layer = False

        # --- Window ---
        self.setWindowTitle(tr("Count Features"))
        self.resize(900, 410)
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

        # --- Clustering parameters group ---
        param_group = QGroupBox(tr("DBSCAN Parameters"))
        param_layout = QFormLayout(param_group)
        param_layout.setLabelAlignment(Qt.AlignLeft)
        param_layout.setFormAlignment(Qt.AlignTop)

        # --- Feature type selection ---
        feature_group = QGroupBox(tr("Feature Types to Count"))
        feature_layout = QVBoxLayout(feature_group)

        # Buildings
        build_layout = QHBoxLayout()
        self.building_check = QCheckBox(tr("Buildings"))
        self.building_check.setChecked(True)
        self.building_check.toggled.connect(self.on_clustering_mode_changed)
        build_layout.addWidget(self.building_check)
        feature_layout.addLayout(build_layout)

        build_out_layout = QHBoxLayout()
        self.building_output = QLineEdit()
        self.building_output.setPlaceholderText(tr("Output for buildings (optional)"))
        build_out_layout.addWidget(self.building_output)
        self.building_button = QPushButton("...")
        self.building_button.setFixedWidth(28)
        self.building_button.setToolTip(tr("Select buildings output file (.gpkg)"))
        build_out_layout.addWidget(self.building_button)
        feature_layout.addLayout(build_out_layout)

        # Trees
        tree_layout = QHBoxLayout()
        self.tree_check = QCheckBox(tr("Trees"))
        self.tree_check.setChecked(False)
        self.tree_check.toggled.connect(self.on_clustering_mode_changed)
        tree_layout.addWidget(self.tree_check)
        feature_layout.addLayout(tree_layout)

        tree_out_layout = QHBoxLayout()
        self.tree_output = QLineEdit()
        self.tree_output.setPlaceholderText(tr("Output for trees (optional)"))
        tree_out_layout.addWidget(self.tree_output)
        self.tree_button = QPushButton("...")
        self.tree_button.setFixedWidth(28)
        self.tree_button.setToolTip(tr("Select trees output file (.gpkg)"))
        tree_out_layout.addWidget(self.tree_button)
        feature_layout.addLayout(tree_out_layout)

        # Bridges
        bridge_layout = QHBoxLayout()
        self.bridge_check = QCheckBox(tr("Bridges"))
        self.bridge_check.setChecked(False)
        self.bridge_check.toggled.connect(self.on_clustering_mode_changed)
        bridge_layout.addWidget(self.bridge_check)
        feature_layout.addLayout(bridge_layout)

        bridge_out_layout = QHBoxLayout()
        self.bridge_output = QLineEdit()
        self.bridge_output.setPlaceholderText(tr("Output for bridges (optional)"))
        bridge_out_layout.addWidget(self.bridge_output)
        self.bridge_button = QPushButton("...")
        self.bridge_button.setFixedWidth(28)
        self.bridge_button.setToolTip(tr("Select bridges output file (.gpkg)"))
        bridge_out_layout.addWidget(self.bridge_button)
        feature_layout.addLayout(bridge_out_layout)

        left_layout.addWidget(feature_group)

        self.building_button.clicked.connect(lambda: self.select_feature_output("buildings"))
        self.tree_button.clicked.connect(lambda: self.select_feature_output("trees"))
        self.bridge_button.clicked.connect(lambda: self.select_feature_output("bridges"))

        self.building_output.textEdited.connect(
            lambda: self.building_output.setModified(True)
        )
        self.tree_output.textEdited.connect(
            lambda: self.tree_output.setModified(True)
        )
        self.bridge_output.textEdited.connect(
            lambda: self.bridge_output.setModified(True)
        )

        # Search radius (eps)
        self.eps_spin = QDoubleSpinBox()
        self.eps_spin.setRange(0.1, 100.0)
        self.eps_spin.setSingleStep(0.1)
        self.eps_spin.setValue(2.0)
        self.eps_spin.setSuffix(self.tr(" units"))
        self.radius_spin.setToolTip(self.tr("Search radius for neighbor detection. The same units are used as the coordinate reference system of the input data."))
        param_layout.addRow(tr("Search radius:"), self.eps_spin)

        # Min samples
        self.min_samples_spin = QSpinBox()
        self.min_samples_spin.setRange(1, 1000)
        self.min_samples_spin.setValue(30)
        param_layout.addRow(tr("Min samples:"), self.min_samples_spin)

        # Z-axis (3D clustering)
        self.use_z_check = QCheckBox(tr("Use Z-axis (3D clustering)"))
        self.use_z_check.setChecked(True)
        self.use_z_check.toggled.connect(self.on_clustering_mode_changed)
        param_layout.addRow("", self.use_z_check)

        left_layout.addWidget(param_group)
        left_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Concave hull target percent (0 = very concave, 1 = convex)
        self.hull_target_spin = QDoubleSpinBox()
        self.hull_target_spin.setRange(0.0, 1.0)
        self.hull_target_spin.setSingleStep(0.05)
        self.hull_target_spin.setValue(0.2)
        param_layout.addRow(tr("Concave hull tightness:"), self.hull_target_spin)

        # Allow holes in hull
        self.hull_allow_holes_check = QCheckBox(tr("Allow holes in hull"))
        self.hull_allow_holes_check.setChecked(False)
        param_layout.addRow("", self.hull_allow_holes_check)

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

        title = self.tr("Feature Count")
        intro = self.tr("This tool estimates the number of features in a LiDAR dataset by clustering points classified by a certain feature type (e.g., buildings, trees, bridges).")
        workflow = self.tr("Workflow:")
        step1 = self.tr("Filters points based on selected feature types.")
        step2 = self.tr("Applies DBSCAN clustering to group nearby points.")
        step3 = self.tr("Creates polygons representing each detected cluster.")
        note = self.tr("The number of detected clusters approximates the total number of features.")

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

        # reset modified flags so defaults follow new input
        self.building_output.setModified(False)
        self.tree_output.setModified(False)
        self.bridge_output.setModified(False)

        self.update_feature_outputs()

    def update_default_output(self):
        if not self.selected_input:
            return
        base_name = os.path.splitext(os.path.basename(self.selected_input))[0]
        if self.building_check.isChecked() and self.tree_check.isChecked():
            type_suffix = "buildings_trees"
        elif self.tree_check.isChecked():
            type_suffix = "trees"
        else:
            type_suffix = "buildings"

        cluster_mode = "3D" if self.use_z_check.isChecked() else "2D"
        suffix = f"{type_suffix}_{cluster_mode}.gpkg"
        default_output = os.path.join(
            os.path.dirname(self.selected_input),
            f"{base_name}_{suffix}"
        )

        self.output_edit.setText(default_output)

    def select_input_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select LiDAR File"), "", self.tr("LiDAR Files (*.las *.laz)")
        )
        if filename:
            self.input_combo.addItem(filename, filename)
            self.input_combo.setCurrentIndex(self.input_combo.count() - 1)
            self.selected_input = filename
            self.is_layer = False
            self.update_default_output()

    def on_clustering_mode_changed(self):
        self.update_feature_outputs()

    # --- Accessors ---
    def get_params(self):
        """Return eps, min_samples, use_z."""
        return (
            self.eps_spin.value(),
            self.min_samples_spin.value(),
            self.use_z_check.isChecked(),
            self.hull_target_spin.value(),
            self.hull_allow_holes_check.isChecked(),
        )

    def get_feature_types(self):
        """Return which features the user wants to count."""
        features = []
        if self.building_check.isChecked():
            features.append("buildings")
        if self.tree_check.isChecked():
            features.append("trees")
        if self.bridge_check.isChecked():
            features.append("bridges")
        return features

    def update_feature_outputs(self):
        if not self.selected_input:
            return

        base_name = os.path.splitext(os.path.basename(self.selected_input))[0]
        cluster_mode = "3D" if self.use_z_check.isChecked() else "2D"
        base_dir = os.path.dirname(self.selected_input)

        # Buildings
        default_buildings = os.path.join(
            base_dir, f"{base_name}_buildings_{cluster_mode}.gpkg"
        )
        if not self.building_output.isModified():
            self.building_output.setText(default_buildings)
        self.building_output.setEnabled(self.building_check.isChecked())

        # Trees
        default_trees = os.path.join(
            base_dir, f"{base_name}_trees_{cluster_mode}.gpkg"
        )
        if not self.tree_output.isModified():
            self.tree_output.setText(default_trees)
        self.tree_output.setEnabled(self.tree_check.isChecked())

        # Bridges
        default_bridges = os.path.join(
            base_dir, f"{base_name}_bridges_{cluster_mode}.gpkg"
        )
        if not self.bridge_output.isModified():
            self.bridge_output.setText(default_bridges)
        self.bridge_output.setEnabled(self.bridge_check.isChecked())

    def get_input_output(self):
        outputs = {}
        if self.building_check.isChecked():
            outputs["buildings"] = self.building_output.text().strip()
        if self.tree_check.isChecked():
            outputs["trees"] = self.tree_output.text().strip()
        if self.bridge_check.isChecked():
            outputs["bridges"] = self.bridge_output.text().strip()
        return self.selected_input, outputs

    def select_feature_output(self, feature):
        if not self.selected_input:
            start_path = ""
        else:
            start_path = os.path.dirname(self.selected_input)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Select Output File"),
            start_path,
            self.tr("GeoPackage (*.gpkg)")
        )
        if not filename:
            return

        if feature == "buildings":
            self.building_output.setText(filename)
        elif feature == "trees":
            self.tree_output.setText(filename)
        elif feature == "bridges":
            self.bridge_output.setText(filename)
