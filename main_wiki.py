
from pathlib import Path

from PySide6.QtWidgets import QWidget, QMainWindow, QApplication

from app.wiki_stuff.display_widgets import DebugView


if __name__ == "__main__":
    app = QApplication()
    app.setStyle("fusion")
    window = QMainWindow()
    widget = QWidget()
    window.setCentralWidget(DebugView(Path("Elden Ring Great Archive", "public")))
    window.show()
    app.exec()

