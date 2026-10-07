import ctypes
import os
from typing import Callable

from PySide6.QtCore import QObject, QTimer

from app.parser.adapter import ParserError, ParserAdapter
from app.parser.models import CCharacterData
from app.parser.wrapper import CharacterData


_DLL_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "compare_avx.dll")

MAX_DELTAS = 10000


class LiveWatcherService(QObject):
    # This sends the list of offsets to the Controller

    def __init__(self, lib: ParserAdapter):
        super().__init__()
        self.lib = lib
        self.timer = QTimer()

    def check_for_changes(self) -> CharacterData:
        return self.lib.parse_character_data_live()

    def start(self, callback: Callable):
        if self.lib.init_live():
            self.timer.timeout.connect(callback)
            self.timer.start(500)
            return True
        return False

    def stop(self):
        self.timer.stop()
        self.lib.close_live()