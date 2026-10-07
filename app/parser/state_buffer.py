import ctypes
import os

from app.data.consts import EVENT_POOL_SIZE
from app.parser.models import CCharacterData, CEventDelta
from app.data.containers import EventDelta, HasItemDelta
from app.data.inventory_state import extract_item_id_set
from app.parser.adapter import ParserAdapter


_DLL_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "compare_avx.dll")

MAX_DELTAS = 10000


class DeltaProvider():
    # This sends the list of offsets to the Controller

    def __init__(self, lib: ParserAdapter):
        super().__init__()
        self.lib = lib
        
        # Keep the pools in memory to compare against
        self.deltas = (CEventDelta * MAX_DELTAS)()
        
    def get_event_deltas(self):
        count = self.lib.parse_deltas(self.deltas, MAX_DELTAS)
        return [EventDelta(self.deltas[i].event_id, self.deltas[i].changed_to) for i in range(count)]
    
    def get_item_deltas(self) -> list[HasItemDelta]:
        # 1. Use the stateless function on both internal buffers
        present, past = self.lib.get_present_past_containers()
        present_set = extract_item_id_set(present)
        past_set = extract_item_id_set(past)

        # 2. Perform set math
        added = present_set - past_set
        removed = past_set - present_set

        # 3. Return deltas
        return [HasItemDelta(eid, True) for eid in added] + \
            [HasItemDelta(eid, False) for eid in removed]