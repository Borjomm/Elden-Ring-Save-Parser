import ctypes

from app.parser.models import CInventoryHeld
from app.data.containers import HasItemDelta
from app.data.consts import MAX_COMMON_ITEMS_INVENTORY, MAX_COMMON_ITEMS_STORAGE, MAX_KEY_ITEMS_INVENTORY, MAX_KEY_ITEMS_STORAGE
from app.data.enums import InventoryType



class Inventory:
    def __init__(self, max_item_count: int):
        self.current = (CInventoryHeld * max_item_count)()
        self._current_count = ctypes.c_uint32(0)
        self.past = (CInventoryHeld * max_item_count)()
        self._past_count = ctypes.c_uint32(0)
        self.max_count = max_item_count

    def update_past(self):
        ctypes.memmove(self.past, self.current, ctypes.sizeof(self.current))
        self._past_count.value = self._current_count.value

    @property
    def current_count(self):
        return self._current_count.value
    
    def get_exist_deltas(self) -> list[HasItemDelta]:
        current_ids = {
            self.current[i].item_id 
            for i in range(self._current_count.value) 
            if self.current[i].item_id != 0
        }

        # 2. Extract unique IDs from the PAST buffer
        past_ids = {
            self.past[i].item_id 
            for i in range(self._past_count.value) 
            if self.past[i].item_id != 0
        }

        deltas = []

        # 3. New Items: Items in Current that were NOT in Past
        for item_id in (current_ids - past_ids):
            deltas.append(HasItemDelta(item_id, True))

        # 4. Removed Items: Items in Past that are NOT in Current
        for item_id in (past_ids - current_ids):
            deltas.append(HasItemDelta(item_id, False))

        return deltas


class InventoryState:
    def __init__(self):
        self._ci = Inventory(MAX_COMMON_ITEMS_INVENTORY)
        self._cs = Inventory(MAX_COMMON_ITEMS_STORAGE)
        self._ki = Inventory(MAX_KEY_ITEMS_INVENTORY)
        self._ks = Inventory(MAX_KEY_ITEMS_STORAGE)
        self.storage = {
            InventoryType.COMMON_INVENTORY: self._ci,
            InventoryType.COMMON_STORAGE: self._cs,
            InventoryType.KEY_INVENTORY: self._ki,
            InventoryType.KEY_STORAGE: self._ks
        }

    def get_inventory(self, inv_type: InventoryType):
        return self.storage[inv_type]
    
    def update_past(self):
        for inv in self.storage.values():
            inv.update_past()

    def prep_for_parse(self):
        return (ctypes.byref(self._ci._current_count), self._ci.current,
                ctypes.byref(self._ki._current_count), self._ki.current,
                ctypes.byref(self._cs._current_count), self._cs.current,
                ctypes.byref(self._ks._current_count), self._ks.current)
    
    def get_exist_deltas(self) -> list[HasItemDelta]:
            # 1. Aggregate ALL item IDs currently in Player possession (Inv + Storage)
            current_total_set = set()
            for inv in self.storage.values():
                # Iterate only up to the count reported by the C library
                for i in range(inv._current_count.value):
                    eid = inv.current[i].item_id
                    if eid != 0:
                        current_total_set.add(eid)

            # 2. Aggregate ALL item IDs previously in Player possession
            past_total_set = set()
            for inv in self.storage.values():
                for i in range(inv._past_count.value):
                    eid = inv.past[i].item_id
                    if eid != 0:
                        past_total_set.add(eid)

            # 3. Calculate Global Differences
            # Added: In current total, but wasn't in past total
            added = current_total_set - past_total_set
            
            # Removed: Was in past total, but isn't in current total
            removed = past_total_set - current_total_set

            # 4. Construct Delta objects
            return ([HasItemDelta(eid, True) for eid in added] + 
                    [HasItemDelta(eid, False) for eid in removed])
