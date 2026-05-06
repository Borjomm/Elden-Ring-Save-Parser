
from pathlib import Path

from PySide6.QtWidgets import QWidget, QMainWindow, QApplication

from app.wiki_stuff.display_widgets import DebugView
from app.infrastructure.settings_repository import SettingsRepository
from app.util import utils


if __name__ == "__main__":
    app = QApplication()
    app.setStyle("fusion")
    window = QMainWindow()
    window.setGeometry(*utils.get_spawn_coordinates())
    widget = QWidget()
    settings = SettingsRepository()
    wiki_settings = settings.get_or_prompt_wiki_settings()
    if wiki_settings:
        window.setCentralWidget(DebugView(wiki_settings))
        window.show()
        app.exec()

