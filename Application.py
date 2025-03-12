import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize

from MainWindow import MainWindow

app = QApplication(sys.argv)

app.setStyle("Windows")

window = MainWindow(app)
window.show()
window.resize(QSize(1280, 720))

app.exec()
