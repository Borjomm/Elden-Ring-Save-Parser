import ctypes
import os
from typing import Callable

from PySide6.QtCore import QObject, QTimer

from app.parser.adapter import ParserError
from app.parser.models import CCharacterData, CEventDelta

_DLL_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "compare_new.dll")

MAX_DELTAS = 10000


class LiveWatcherService(QObject):
    # This sends the list of offsets to the Controller

    def __init__(self):
        super().__init__()
        self._load_dll()
        self._present = CCharacterData()
        self.timer = QTimer()
        
        # Keep the pools in memory to compare against
        self.deltas = (CEventDelta * MAX_DELTAS)()

    def _load_dll(self):
        self.lib = ctypes.CDLL(_DLL_PATH)
        self.lib.init.restype = ctypes.c_bool
        self.lib.parse_character_data.argtypes = [ctypes.POINTER(CCharacterData)]
        self.lib.parse_character_data.restype = ctypes.c_bool



    def check_for_changes(self):
        # 1. Big Gulp
        success = self.lib.parse_character_data(ctypes.byref(self._present))
        if not success:
            self.stop()
            self.lib.close()
            raise ParserError("Connection severed. Elden Ring closed")
        return CCharacterData.from_buffer_copy(self._present)

    def start(self, callback: Callable):
        if self.lib.init():
            self.timer.timeout.connect(callback)
            self.timer.start(500)
            return True
        return False

    def stop(self):
        self.timer.stop()
        self.lib.close()