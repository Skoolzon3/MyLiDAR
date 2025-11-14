from qgis.core import QgsProject, QgsPointCloudLayer, QgsMessageLog, Qgis, QgsColorRampShader, QgsPointCloudClassifiedRenderer
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,QDialogButtonBox, QFileDialog, QLineEdit, QSizePolicy, QTextBrowser, QWidget, QGroupBox, QGridLayout, QCheckBox
import laspy
import numpy as np
import os

class PointFilteringDialog(QDialog):
    """Dialog window for point filtering settings."""

    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.tr = translator if translator else (lambda s: s)
        self.selected_input = None
        self.selected_output = None
        self.is_layer = False
        self.user_edited_output = False
        self.class_checkboxes = {}

        # --- Window ---
        self.setWindowTitle(self.tr("Filter Points by Classification"))
        self.resize(850, 500)
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
        param_group = QGroupBox(self.tr("Point Filtering"))
        self.param_layout = QGridLayout(param_group)
        self.param_layout.setColumnStretch(0, 1)
        self.param_layout.setColumnStretch(1, 1)
        left_layout.addWidget(param_group)

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

        title = self.tr("Point Filtering")
        intro = self.tr(
            "This tool filters LiDAR points based on their classification codes. Users can select one or more classification classes to remove from the dataset."
        )
        workflow = self.tr("Workflow:")
        step1 = self.tr("Reads the input LAS/LAZ file and extracts point classification values.")
        step2 = self.tr("Applies the user-defined filtering rule to remove the selected classes.")
        step3 = self.tr("Creates a new LAS/LAZ file containing only the filtered points.")
        note = self.tr(
            "The resulting LiDAR file will include only the desired classification codes, allowing users to isolate specific features (e.g., ground or vegetation) or remove unwanted data."
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

        self.populate_class_list()

    def update_default_output(self):
        """Auto-generate default output file path."""
        if not self.selected_input:
            return
        base_name = os.path.splitext(os.path.basename(self.selected_input))[0]
        default_output = os.path.join(
            os.path.dirname(self.selected_input),
            base_name + "_filtered.laz"
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
            self.tr("Save Filtered LiDAR File"),
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

    def get_filter_settings(self):
        """Return list of selected classification codes."""
        if not hasattr(self, "class_checkboxes"):
            return []

        selected = [code for code, cb in self.class_checkboxes.items() if cb.isChecked()]
        return selected

    def get_classifications_from_file(self, filepath):
        """Return (class_code, count) pairs from a LAS/LAZ file."""
        try:
            with laspy.open(filepath) as f:
                all_classes = []
                for points in f.chunk_iterator(4_000_000):
                    all_classes.append(points.classification)
                classes, counts = np.unique(np.concatenate(all_classes), return_counts=True)
            return list(zip(classes.tolist(), counts.tolist()))
        except Exception as e:
            QgsMessageLog.logMessage(
                f"{self.tr('Error reading classifications from')} {filepath}: {e}",
                "PointFilter",
                Qgis.Warning
            )
            return []

    def populate_class_list(self):
        """Populate classification checkboxes in two columns with colors."""
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.selected_input or not os.path.exists(self.selected_input):
            return

        # Get per-class counts
        present_classes = self.get_classifications_from_file(self.selected_input)
        if not present_classes:
            label = QLabel(self.tr("(No classification data found)"))
            label.setStyleSheet("color: gray; font-style: italic;")
            self.param_layout.addWidget(label, 0, 0)
            return

        class_colors = self.get_class_colors_from_layer(self.input_combo.itemData(self.input_combo.currentIndex()))

        fallback_colors = {
            0: (self.tr("Created, Never Classified"), "#A0A0A0"),
            1: (self.tr("Unclassified"), "#AAAAAA"),
            2: (self.tr("Ground"), "#AA5500"),
            3: (self.tr("Low Vegetation"), "#00AAAA"),
            4: (self.tr("Medium Vegetation"), "#55FF55"),
            5: (self.tr("High Vegetation"), "#00AA00"),
            6: (self.tr("Building"), "#FF5555"),
            7: (self.tr("Low Point (Noise)"), "#AA0000"),
            8: (self.tr("Model Key-point"), "#FFD700"),
            9: (self.tr("Water"), "#55FFFF"),
            10: (self.tr("Rail"), "#AA00AA"),
            11: (self.tr("Road Surface"), "#A0522D"),
            12: (self.tr("Overlap"), "#555555"),
            13: (self.tr("Wire Guard"), "#00CED1"),
            14: (self.tr("Wire Conductor"), "#20B2AA"),
            15: (self.tr("Transmission Tower"), "#000080"),
            16: (self.tr("Wire-structure Connector"), "#708090"),
            17: (self.tr("Bridge Deck"), "#5555FF"),
            18: (self.tr("High Noise"), "#646464"),
        }

        default_checked = {7, 12, 18}

        self.class_checkboxes = {}
        for idx, (class_code, count) in enumerate(sorted(present_classes, key=lambda x: x[0])):
            if class_code in class_colors:
                name = f"{self.tr('Class')} {class_code}"
                color = class_colors[class_code]
            else:
                name, color = fallback_colors.get(class_code, (f"{self.tr('Unknown')} ({class_code})", "#CCCCCC"))

            row, col = divmod(idx, 2)
            color_label = QLabel()
            color_label.setFixedSize(14, 14)
            color_label.setStyleSheet(f"background-color: {color}; border: 1px solid #555; border-radius: 2px;")

            if class_code in class_colors:
                label_text = f"{class_code} - {name} - {count}"
            else:
                label_text = f"{class_code} - {name} - {count}"

            cb = QCheckBox(label_text)

            if class_code in default_checked:
                cb.setChecked(True)

            self.class_checkboxes[class_code] = cb

            hbox = QHBoxLayout()
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.setSpacing(6)
            hbox.addWidget(color_label)
            hbox.addWidget(cb)
            hbox.addStretch()

            container = QWidget()
            container.setLayout(hbox)
            self.param_layout.addWidget(container, row, col)

    def get_class_colors_from_layer(self, layer):
        """Return a dict {class_code: #RRGGBB} from the layer's renderer when possible."""
        color_dict = {}

        QgsMessageLog.logMessage(
            self.tr("Reading classification colors from layer..."),
            "PointFilter", Qgis.Info
        )

        try:
            if not isinstance(layer, QgsPointCloudLayer):
                QgsMessageLog.logMessage(
                    self.tr("Layer is not a QgsPointCloudLayer."),
                    "PointFilter", Qgis.Warning
                )
                return {}

            renderer = layer.renderer()
            if not renderer:
                QgsMessageLog.logMessage(
                    self.tr("Renderer is missing on the layer."),
                    "PointFilter", Qgis.Warning
                )
                return {}

            QgsMessageLog.logMessage(
                f"{self.tr('Renderer detected')}: {renderer.__class__.__name__}",
                "PointFilter", Qgis.Info
            )

            # --- Handle classified renderer ---
            if isinstance(renderer, QgsPointCloudClassifiedRenderer):
                QgsMessageLog.logMessage(
                    self.tr("Using QgsPointCloudClassifiedRenderer"),
                    "PointFilter", Qgis.Info
                )
                categories = renderer.categories()
                QgsMessageLog.logMessage(
                    f"{self.tr('Category count')}: {len(categories)}",
                    "PointFilter", Qgis.Info
                )
                for cat in categories:
                    try:
                        code = int(cat.value())
                    except Exception:
                        continue

                    qcolor = cat.color()
                    hex_color = qcolor.name(QColor.HexRgb).upper()
                    color_dict[code] = hex_color
                    QgsMessageLog.logMessage(
                        f"{self.tr('Class color extracted')}: {code} → {hex_color}",
                        "PointFilter", Qgis.Info
                    )

                if color_dict:
                    return color_dict

            # --- Fallback: Shader (classification uses color ramp rules) ---
            if hasattr(renderer, "shader"):
                shader = renderer.shader()
                if shader:
                    QgsMessageLog.logMessage(
                        self.tr("Trying fallback: shader color ramp"),
                        "PointFilter", Qgis.Info
                    )
                    for item in shader.colorRampItemList():
                        try:
                            code = int(item.value)
                        except Exception:
                            continue
                        hex_color = item.color.name(QColor.HexRgb).upper()
                        color_dict[code] = hex_color
                        QgsMessageLog.logMessage(
                            f"{self.tr('Shader color assigned')}: {code} -> {hex_color}",
                            "PointFilter", Qgis.Info
                        )

            return color_dict

        except Exception as e:
            QgsMessageLog.logMessage(
                f"{self.tr('Error reading class colors from layer')}: {e}",
                "PointFilter", Qgis.Warning
            )
            return {}
