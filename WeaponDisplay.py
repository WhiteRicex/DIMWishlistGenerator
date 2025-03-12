from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QPushButton
)

class WeaponDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QHBoxLayout()

        #image

        self.GenerateColumn(4) #barrel
        self.GenerateColumn(4) #mag
        self.GenerateColumn(4) #perk 1
        self.GenerateColumn(4) #perk 2

        self.mainLayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.mainLayout)

    def GenerateColumn(self, itemCount):
        column = QVBoxLayout()

        for i in range(itemCount):
            column.addWidget(QPushButton(str(i)))

        self.mainLayout.addLayout(column)