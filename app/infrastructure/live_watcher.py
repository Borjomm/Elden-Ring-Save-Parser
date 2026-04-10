from PySide6.QtCore import QObject, QTimer
import ctypes
from app.core.app_state import event_bus

class FlagChange(ctypes.Structure):
    _fields_ = [("event_id", ctypes.c_uint32), ("bit_offset", ctypes.c_uint32),
                ("old_state", ctypes.c_bool), ("new_state", ctypes.c_bool)]

class LiveWatcherService(QObject):
    def __init__(self):
        super().__init__()
        # Load your live memory DLL here
        self.er_lib = ctypes.CDLL("er_live_memory.dll")
        self.er_lib.get_flag_changes.restype = ctypes.c_int
        
        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self._poll_memory)
        
        self.buffer = (FlagChange * 1000)()

    def start_watching(self):
        if self.er_lib.init_session():
            self.timer.start()
            return True
        return False

    def stop_watching(self):
        self.timer.stop()
        self.er_lib.close_session()

    def _poll_memory(self):
        num_changes = self.er_lib.get_flag_changes(self.buffer, 1000)
        if num_changes > 0:
            for i in range(num_changes):
                change = self.buffer[i]
                
                # Check for the system "Loading" flag (assuming offset 2000 is it)
                if change.bit_offset == 2000:
                    event_bus.live_loading_state_changed.emit(change.new_state)
                    continue
                
                # Emit to the UI!
                event_bus.flag_changed.emit(change.bit_offset, change.new_state)