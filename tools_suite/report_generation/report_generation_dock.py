# --- General imports ---
import io

# --- QGIS and PyQt imports ---
from qgis.PyQt.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel, QScrollArea, QTextEdit, QPushButton, QDialog, QVBoxLayout as QVLayout
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap

# --- Method-specific imports ---
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

class ReportDock(QDockWidget):
    def __init__(self, parent=None, translator=None):
        self.tr = translator if translator else (lambda s: s)
        super().__init__(self.tr("LiDAR Statistics"), parent)

        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.container)
        self.setWidget(scroll)

    def clear(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def add_text(self, text: str):
        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        text_widget.setPlainText(text)
        text_widget.setMinimumHeight(200)

        text_widget.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                font-family: Consolas, 'Courier New', monospace;
                background-color: #f9f9f9;
            }
        """)

        self.layout.addWidget(text_widget)

    def add_button_for_figure(self, fig, title=""):
        btn = QPushButton(f"{self.tr('View')} {title}")
        btn.clicked.connect(lambda _, f=fig, t=title: self.show_popup(f, t))
        self.layout.addWidget(btn)

    def show_popup(self, fig, title=""):
        dialog = QDialog(self)
        dialog.setWindowTitle(title if title else "Figure")

        canvas = FigureCanvas(fig)
        buf = io.BytesIO()
        canvas.print_png(buf)

        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue(), "PNG")

        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        vbox = QVLayout(dialog)
        vbox.addWidget(label)
        dialog.setLayout(vbox)

        dialog.resize(pixmap.width(), pixmap.height())
        dialog.exec_()
