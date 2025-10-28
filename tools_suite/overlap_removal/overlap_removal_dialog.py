from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,QDialogButtonBox, QFileDialog, QLineEdit, QSizePolicy, QTextBrowser, QWidget, QSpacerItem
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject, QgsPointCloudLayer
import os

class OverlapRemovalDialog(QDialog):
    def __init__(self, parent=None, tr=lambda s: s):
        super().__init__(parent)
        self.tr = tr
        self.selected_input = None
        self.selected_output = None
        self.is_layer = False
        self.user_edited_output = False

        # --- Window ---
        self.setWindowTitle(tr("Remove Overlap Points"))
        self.resize(850, 400)
        self.setMinimumWidth(800)

        # --- Layout ---
        main_layout = QHBoxLayout(self)

        # --- Left Panel (Inputs) ---
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
        left_layout.addWidget(QLabel(tr("Output file:")))
        output_layout = QHBoxLayout()

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText(tr("Select output file path..."))
        output_layout.addWidget(self.output_edit)

        self.output_button = QPushButton("...")
        self.output_button.setToolTip(tr("Select output file (.las / .laz)"))
        self.output_button.setFixedWidth(28)
        self.output_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        output_layout.addWidget(self.output_button)
        left_layout.addLayout(output_layout)

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

        # icon_path = os.path.join(os.path.dirname(__file__),"..","..","icons","overlap.png")
        # icon_path = os.path.abspath(icon_path)

        # <!-- Icon in top-right corner -->
        # <img src="file:///{icon_path}"
        #      style="position: absolute; top: 4px; right: 4px; width: 24px; height: 24px;"
        #      alt="Icon">

        title = self.tr("Overlap Removal")
        intro = self.tr(
            "This tool removes overlap points from a LiDAR file based on classification codes. "
            "Points classified as overlap are filtered out, and the remaining points are saved as a new point cloud."
        )
        workflow = self.tr("Workflow:")
        step1 = self.tr("Reads the input .las or .laz file.")
        step2 = self.tr("Filters out points with overlap classification codes (12, 17).")
        step3 = self.tr("Writes the cleaned point cloud to a new file.")
        note = self.tr("The resulting dataset contains only non-overlapping LiDAR points.")

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
        """Update selected input when a layer is chosen and update output path."""
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
        """Generate a default output path based on current input."""
        if not self.selected_input:
            return

        if self.is_layer:
            base_name = os.path.splitext(os.path.basename(self.selected_input))[0]
        else:
            base_name = os.path.splitext(os.path.basename(self.selected_input))[0]

        default_output = os.path.join(
            os.path.dirname(self.selected_input),
            base_name + "_non_overlap.laz"
        )

        self.output_edit.setText(default_output)
        self.selected_output = default_output

    def select_input_file(self):
        """Open file dialog for input selection."""
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
        """Open file dialog for output selection."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save Non-Overlap LiDAR File"),
            self.output_edit.text() or "",
            self.tr("LiDAR Files (*.las *.laz)")
        )
        if filename:
            self.output_edit.setText(filename)
            self.selected_output = filename
            self.user_edited_output = True

    def get_input_output(self):
        """Return tuple (input_path, output_path)."""
        input_path = self.selected_input
        output_path = self.output_edit.text().strip()
        return input_path, output_path
