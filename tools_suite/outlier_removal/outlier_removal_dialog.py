from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,QDialogButtonBox, QFileDialog, QLineEdit, QSizePolicy, QTextBrowser, QWidget, QSpacerItem, QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsPointCloudLayer
import os

class OutlierRemovalDialog(QDialog):
    """Dialog window for outlier removal settings."""

    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.tr = translator if translator else (lambda s: s)
        self.selected_input = None
        self.selected_output = None
        self.is_layer = False
        self.user_edited_output = False

        # --- Window ---
        self.setWindowTitle(self.tr("Remove Outlier Points"))
        self.resize(850, 440)
        self.setMinimumWidth(800)

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
        self.input_combo.setEditable(False)
        input_layout.addWidget(self.input_combo)

        self.input_button = QPushButton("...")
        self.input_button.setToolTip(self.tr("Select input file (.las / .laz)"))
        self.input_button.setFixedWidth(28)
        self.input_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        input_layout.addWidget(self.input_button)
        left_layout.addLayout(input_layout)

        # --- Output selection ---
        left_layout.addWidget(QLabel(self.tr("Output file:")))
        output_layout = QHBoxLayout()

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(self.tr("Select output file path..."))
        output_layout.addWidget(self.output_edit)

        self.output_button = QPushButton("...")
        self.output_button.setToolTip(self.tr("Select output file (.las / .laz)"))
        self.output_button.setFixedWidth(28)
        self.output_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        output_layout.addWidget(self.output_button)
        left_layout.addLayout(output_layout)

        # --- Parameters group ---
        param_group = QGroupBox(self.tr("Outlier Removal Parameters"))
        param_layout = QFormLayout(param_group)
        param_layout.setLabelAlignment(Qt.AlignRight)

        # Search radius
        self.radius_spin = QDoubleSpinBox()
        self.radius_spin.setRange(0.01, 50.0)
        self.radius_spin.setSingleStep(0.1)
        self.radius_spin.setValue(2.0)
        self.radius_spin.setDecimals(2)
        self.radius_spin.setSuffix(" m")
        param_layout.addRow(self.tr("Search radius:"), self.radius_spin)

        # Min neighbors
        self.min_neighbors_spin = QSpinBox()
        self.min_neighbors_spin.setRange(1, 1000)
        self.min_neighbors_spin.setSingleStep(1)
        self.min_neighbors_spin.setValue(5)
        param_layout.addRow(self.tr("Minimum neighbors:"), self.min_neighbors_spin)

        left_layout.addWidget(param_group)
        left_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- OK / Cancel buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        left_layout.addWidget(buttons)

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

        title = self.tr("Outlier Removal")
        intro = self.tr(
            "This tool removes isolated points (outliers) from a LiDAR dataset. "
            "By using a radius-based neighbor search, it detects points that have "
            "too few nearby neighbors within a given distance."
        )
        workflow = self.tr("Workflow:")
        step1 = self.tr("Builds a KD-tree from all points in the cloud.")
        step2 = self.tr("Counts neighbors within a specified radius.")
        step3 = self.tr("Removes points with fewer than minimum neighbors.")
        note = self.tr(
            "Adjust the parameters to control how strictly isolated points are removed. "
            "Smaller radius or higher neighbor counts will remove more points."
        )

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
        """Populate combo with loaded LiDAR layers, selecting first if any."""
        self.input_combo.clear()
        layers = [
            layer for layer in QgsProject.instance().mapLayers().values()
            if isinstance(layer, QgsPointCloudLayer)
        ]
        if not layers:
            self.selected_input = None
            self.is_layer = False
            return

        for layer in layers:
            crs = f" [{layer.crs().authid()}]" if layer.crs().isValid() else ""
            self.input_combo.addItem(f"{layer.name()}{crs}", layer)
        self.input_combo.setCurrentIndex(0)
        self.on_input_changed(0)

    def on_input_changed(self, index):
        """Update selected input when a layer is chosen."""
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
        """Auto-generate default output file path."""
        if not self.selected_input:
            return
        base_name = os.path.splitext(os.path.basename(self.selected_input))[0]
        default_output = os.path.join(
            os.path.dirname(self.selected_input),
            base_name + "_cleaned.laz"
        )
        self.output_edit.setText(default_output)
        self.selected_output = default_output

    def select_input_file(self):
        """Open dialog to choose input LiDAR file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select LiDAR File"),
            "",
            self.tr("LiDAR Files (*.las *.laz)")
        )
        if filename:
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
        """Open dialog to select output LiDAR file path."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Cleaned LiDAR File"),
            self.output_edit.text() or "",
            self.tr("LiDAR Files (*.las *.laz)")
        )
        if filename:
            self.output_edit.setText(filename)
            self.selected_output = filename
            self.user_edited_output = True

    def get_values(self):
        """Return radius and min_neighbors as tuple."""
        radius = self.radius_spin.value()
        min_neighbors = self.min_neighbors_spin.value()
        return radius, min_neighbors

    def get_input_output(self):
        """Return (input_path, output_path)."""
        return self.selected_input, self.output_edit.text().strip()
