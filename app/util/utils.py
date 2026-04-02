from typing import Optional, Callable

from PySide6.QtWidgets import QWidget, QComboBox, QVBoxLayout, QLabel, QMessageBox
from PySide6.QtGui import QGuiApplication, QAction, QKeySequence
from PySide6.QtCore import QObject

def get_spawn_coordinates(width: int, height: int):
    screen = QGuiApplication.primaryScreen()  # Получаем основной экран
    wwidth = screen.geometry().width()  # Получаем геометрию экрана
    wheight = screen.geometry().height()
    geometry = ((wwidth-width)//2, (wheight-height)//2, width, height)
    return geometry

def make_action(parent: QObject, name: str, handler: Callable, key_sequence: Optional[str] = None) -> QAction:
    action = QAction(name, parent)
    if key_sequence:
        action.setShortcut(QKeySequence(key_sequence))
    action.triggered.connect(handler)
    return action

def make_combo_widget(label_str: str, item_list: list, handler: Callable, current_index: int) -> QWidget:
    widget = QWidget()
    label = QLabel(label_str)
    box = QComboBox()
    box.addItems(item_list)
    box.setCurrentIndex(current_index)
    box.currentIndexChanged.connect(handler)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(box)
    widget.setLayout(layout)
    return widget


def display_alert(error_msg: str):
    msg = QMessageBox(text = error_msg, icon = QMessageBox.Icon.Critical)
    msg.exec()
