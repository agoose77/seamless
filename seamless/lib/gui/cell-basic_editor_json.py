from seamless.qt.QtWidgets import QTextEdit, QWidget, QVBoxLayout
from seamless.qt.QtCore import Qt
from PyQt5.QtGui import QColor
import json

w = QWidget()
#w.setWindowFlags(Qt.WindowStaysOnTopHint)
w.setAttribute(Qt.WA_ShowWithoutActivating)
vbox = QVBoxLayout()
#vbox.addStretch(1)
w.resize(600,600)
w.setLayout(vbox)
w.setWindowTitle(PINS.title.get())

class MyTextEdit(QTextEdit):
    def focusOutEvent(self, event):
        PINS.value.set(self.toPlainText())
        QTextEdit.focusOutEvent(self, event)

w.show()
b = MyTextEdit()
b.setFontPointSize(15)
if PINS.value.defined:
    b.setText(json.dumps(PINS.value.get(), indent=2))
#b.setFontItalic(True)
#b.setTextColor(QColor(255,0,0))
vbox.addWidget(b)
