from typing import Callable

from PySide6.QtCore import QObject, QTimer

from app.parser.adapter import ParserAdapter
from app.parser.wrapper import CharacterData


class LiveWatcherService(QObject):
    # This sends the list of offsets to the Controller

    def __init__(self, lib: ParserAdapter):
        super().__init__()
        self.lib = lib
        self.callback = None
        self.timer = QTimer()

    def check_for_changes(self) -> CharacterData:
        return self.lib.parse_character_data_live()

    def start(self, callback: Callable):
        if self.lib.init_live():
            self.callback = callback
            self.timer.timeout.connect(callback)
            self.timer.start(500)
            return True
        return False

    def stop(self):
        self.timer.stop()
        if self.callback is not None:
            self.timer.timeout.disconnect(self.callback)
            self.callback = None
        self.lib.close_live()