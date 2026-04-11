import ctypes
import os
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal

from app.core.app_state import event_bus
from app.parser.adapter import ParserError
from app.data.containers import Delta

_DLL_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "compare.dll")

class EventDelta(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("event_id", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("changed_to", ctypes.c_bool)
    ]

POOL_SIZE = 1833375
MAX_DELTAS = 10000

class LiveWatcherService(QObject):
    # This sends the list of offsets to the Controller
    delta_detected = Signal(Delta)

    def __init__(self):
        super().__init__()
        self._load_dll()
        self.timer = QTimer()
        
        # Keep the pools in memory to compare against
        self.current_pool = (ctypes.c_ubyte * POOL_SIZE)()
        self.past_pool = (ctypes.c_ubyte * POOL_SIZE)()
        self.deltas = (EventDelta * MAX_DELTAS)()

    def _load_dll(self):
        self.lib = ctypes.CDLL(_DLL_PATH)
        self.lib.init.restype = ctypes.c_bool
        self.lib.fill_flags.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
        self.lib.fill_flags.restype = ctypes.c_bool
        self.lib.get_deltas.argtypes = [ctypes.POINTER(EventDelta), ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
        self.lib.get_deltas.restype = ctypes.c_int

    def check_for_changes(self, supress_signal: bool = False):
        # 1. Big Gulp
        if self.lib.fill_flags(self.current_pool, POOL_SIZE):
            # 2. Get Deltas
            count = self.lib.get_deltas(self.deltas, MAX_DELTAS, self.current_pool, self.past_pool, POOL_SIZE)
            
            if count > 0:
                # Convert to a simple Python list of offsets
                if not supress_signal:
                    deltas = [Delta(self.deltas[i].event_id, self.deltas[i].offset, self.deltas[i].changed_to) for i in range(count)]
                    self.delta_detected.emit(deltas)
            
            # 3. Swap pools (efficient way to update past_pool)
            ctypes.memmove(self.past_pool, self.current_pool, POOL_SIZE)
        else:
            self.stop()
            self.lib.close()
            raise ParserError("Connection severed. Elden Ring closed")

    def get_current_flags_bytes(self) -> bytes:
        """Returns a fresh copy of the current memory pool as Python bytes."""
        return bytes(self.current_pool)

    def start(self, callback: Callable):
        if self.lib.init():
            self.timer.timeout.connect(callback)
            self.timer.start(500)
            return True
        return False

    def stop(self):
        self.timer.stop()