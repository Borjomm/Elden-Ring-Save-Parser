import ctypes
import os

from app.data.consts import EVENT_POOL_SIZE
from app.parser.models import CCharacterData, CEventDelta
from app.data.containers import EventDelta, HasItemDelta
from app.data.inventory_state import extract_item_id_set

_DLL_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "compare_new.dll")

MAX_DELTAS = 10000


class DeltaProvider():
    # This sends the list of offsets to the Controller

    def __init__(self):
        super().__init__()
        self._load_dll()
        self._past = CCharacterData()
        self._present = CCharacterData()
        
        # Keep the pools in memory to compare against
        self.deltas = (CEventDelta * MAX_DELTAS)()

    def update(self, new_data: CCharacterData):
        ctypes.memmove(ctypes.byref(self._past), ctypes.byref(self._present), ctypes.sizeof(CCharacterData))
        self._present = new_data

    def _load_dll(self):
        self.lib = ctypes.CDLL(_DLL_PATH)
        self.lib.get_deltas.argtypes = [ctypes.POINTER(CEventDelta), ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
        self.lib.get_deltas.restype = ctypes.c_int
        
    def get_event_deltas(self):
        count = self.lib.get_deltas(self.deltas, MAX_DELTAS, self._present.eventFlags, self._past.eventFlags, EVENT_POOL_SIZE)
        return [EventDelta(self.deltas[i].event_id, self.deltas[i].changed_to) for i in range(count)]
    
    def get_item_deltas(self) -> list[HasItemDelta]:
        # 1. Use the stateless function on both internal buffers
        present_set = extract_item_id_set(self._present)
        past_set = extract_item_id_set(self._past)

        # 2. Perform set math
        added = present_set - past_set
        removed = past_set - present_set

        # 3. Return deltas
        return [HasItemDelta(eid, True) for eid in added] + \
            [HasItemDelta(eid, False) for eid in removed]