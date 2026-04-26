from typing import Optional, Callable
from pathlib import Path
import time
import shutil
from PySide6.QtWidgets import QWidget, QComboBox, QVBoxLayout, QLabel, QMessageBox
from PySide6.QtGui import QGuiApplication, QAction, QKeySequence, QCursor
from PySide6.QtCore import QObject, Qt

def get_spawn_coordinates(scale: float = 0.6):
    screen = QGuiApplication.screenAt(QCursor.pos())

    if not screen:
        screen = QGuiApplication.primaryScreen()

    geo = screen.availableGeometry()

    width = int(geo.width() * scale)
    height = int(geo.height() * scale)

    x = geo.x() + (geo.width() - width) // 2
    y = geo.y() + (geo.height() - height) // 2

    return x, y, width, height

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

def make_small_screenshot(width: int = 720, height: int = 480):
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return None
    pixmap = screen.grabWindow(0)
    small = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return small

def make_small_screenshot_and_save(path: str, width: int = 720, height: int = 480):
    small = make_small_screenshot(width, height)
    if small is not None:
        small.save(path, "JPG", quality=80)
        return True
    return False

def init_dirs() -> None:
    Path("tmp/screenshots").mkdir(parents=True, exist_ok=True)

def regenerate_temp():
    for _ in range(5): # Try 5 times
        try:
            shutil.rmtree(Path("tmp"))
            init_dirs()
            return True
        except PermissionError:
            time.sleep(0.2) # Wait for OS to release lock
    return False




