from PyQt5.QtWidgets import QAction, QMessageBox, QMenu
from PyQt5.QtGui import QIcon

def classFactory(iface):
    return MyLiDAR(iface)

class MyLiDAR:
    def __init__(self, iface):
        self.iface = iface
        self.menu = 'MyLiDAR menu'
        self.actions = []

    def initGui(self):
        # self.action = QAction('Go!', self.iface.mainWindow())
        # self.action.triggered.connect(self.run)
        # self.iface.addToolBarIcon(self.action)

        # Create action for classifying LiDAR
        self.classify_action = QAction(QIcon(), 'MyLiDAR', self.iface.mainWindow())
        self.classify_action.triggered.connect(self.classify_lidar)

        # Add to QGIS plugin menu
        self.iface.addPluginToMenu(self.menu, self.classify_action)
        self.actions.append(self.classify_action)

        # Optional: Add to toolbar
        self.iface.addToolBarIcon(self.classify_action)

    def unload(self):
        # self.iface.removeToolBarIcon(self.action)
        # del self.action

        # Remove all actions from menu and toolbar
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        self.actions.clear()

    def classify_lidar(self):
        # Classification logic
        QMessageBox.information(None, 'LiDAR Classification', 'Gibraltar español')
