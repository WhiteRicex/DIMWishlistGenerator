from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
)

from PySide6.QtGui import(
    QPixmap
)

import requests

class ItemSlot(QWidget):
    def __init__(self, weaponData):
        super().__init__()
        mainLayout = QHBoxLayout()
        self.weaponHash = weaponData["hash"]

        label = QLabel(self)
        
        request = requests.get("https://www.bungie.net"+weaponData["displayProperties"]["icon"])
        pixmap = QPixmap()
        pixmap.loadFromData(request.content)
        label.setPixmap(pixmap)
        mainLayout.addWidget(label)

        self.itemButton = QPushButton(weaponData["displayProperties"]["name"])
        mainLayout.addWidget(self.itemButton)

        mainLayout.setContentsMargins(0,0,0,0)
        self.setLayout(mainLayout)
    