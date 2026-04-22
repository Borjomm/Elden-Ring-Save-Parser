import ctypes
import os
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal

from app.data.consts import EVENT_POOL_SIZE
from app.parser.adapter import ParserError
from app.parser.models import CInventoryHeld
from app.data.containers import EventDelta
from app.data.inventory_state import InventoryState

_DLL_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "compare_new.dll")

class CEventDelta(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("event_id", ctypes.c_uint32),
        ("changed_to", ctypes.c_bool)
    ]

MAX_DELTAS = 10000


class LiveWatcherService(QObject):
    # This sends the list of offsets to the Controller
    event_delta_detected = Signal(EventDelta)

    def __init__(self):
        super().__init__()
        self._load_dll()
        self.timer = QTimer()
        
        # Keep the pools in memory to compare against
        self.current_event_pool = (ctypes.c_ubyte * EVENT_POOL_SIZE)()
        self.past_event_pool = (ctypes.c_ubyte * EVENT_POOL_SIZE)()
        self.deltas = (CEventDelta * MAX_DELTAS)()

        self.inventory_state = InventoryState()

    def _load_dll(self):
        self.lib = ctypes.CDLL(_DLL_PATH)
        self.lib.init.restype = ctypes.c_bool
        self.lib.fill_flags.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
        self.lib.fill_flags.restype = ctypes.c_bool
        self.lib.get_deltas.argtypes = [ctypes.POINTER(CEventDelta), ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
        self.lib.get_deltas.restype = ctypes.c_int
        self.lib.parse_items.argtypes = [ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(CInventoryHeld), 
                                         ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(CInventoryHeld), 
                                         ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(CInventoryHeld), 
                                         ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(CInventoryHeld)]
        self.lib.parse_items.restype = ctypes.c_bool


    def check_for_changes(self, supress_signal: bool = False):
        # 1. Big Gulp
        if self.lib.fill_flags(self.current_event_pool, EVENT_POOL_SIZE):
            if not supress_signal:
                count = self.lib.get_deltas(self.deltas, MAX_DELTAS, self.current_event_pool, self.past_event_pool, EVENT_POOL_SIZE)
                
                if count > 0:
                    # Convert to a simple Python list of offsets
                    deltas = [EventDelta(self.deltas[i].event_id, self.deltas[i].changed_to) for i in range(count)]
                    self.event_delta_detected.emit(deltas)
            
            # 3. Swap pools (efficient way to update past_pool)
            ctypes.memmove(self.past_event_pool, self.current_event_pool, EVENT_POOL_SIZE)
        else:
            self.stop()
            self.lib.close()
            raise ParserError("Connection severed. Elden Ring closed")
        


    def get_current_flags_bytes(self) -> bytes:
        """Returns a fresh copy of the current memory pool as Python bytes."""
        return bytes(self.current_event_pool)

    def start(self, callback: Callable):
        if self.lib.init():
            self.timer.timeout.connect(callback)
            self.timer.start(500)
            return True
        return False

    def stop(self):
        self.timer.stop()