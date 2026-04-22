from sqlite3 import Connection
import time
import json
from pathlib import Path
from datetime import datetime
from app.data.containers import EventDelta, EventFlag, DisplayedDeltaChange, HasItemDelta
from app.data.consts import REGION_FLAGS, REGION_MAP
from app.util.utils import make_small_screenshot_and_save
from PySide6.QtCore import QObject, Signal

def get_int_len(i: int) -> int:
    l = 0
    while i != 0:
        i //= 10
        l += 1
    return l

def get_str_region(region: int) -> str:
    s = str(region)
    return "_".join(s[i:i+2] for i in range(0, len(s), 2))

def screenshot_name(screenshot_id: int, ext: str = "jpg") -> str:
    dt = datetime.fromtimestamp(screenshot_id / 1000)
    return dt.strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3] + f".{ext}"

class EventTracker(QObject):
    new_change_recorded = Signal(object)
    def __init__(self, db_connection: Connection):
        super().__init__()
        with open("D:\\Python\\save_parser\\extraction&testing\\util\\item_dict.json", "r", encoding="utf-8") as f:
            self.item_dict = json.load(f)

        self.db_connection = db_connection
        cursor = self.db_connection.cursor()
        
        cursor.execute("SELECT * FROM event_dictionary")
        rows = cursor.fetchall()
        self.flags: dict[int, EventFlag] = {event_id: EventFlag(event_id, description, category, tags) for event_id, description, category, tags in rows}
        self.new_regions: dict[int, str] = {}

    def _region_flag_helper(self, flag: int) -> str:
        for beginning, flag_range, representation in REGION_FLAGS:
            if beginning <= flag < beginning + flag_range:
                return representation
        return "Unknown Flag"
    
    def _map_region_flag(self, flag: int, flag_len: int):
        match flag_len:
            case 10:
                region = (600000 + (((flag // 100000000) % 10) * 10000)) + ((flag // 10000) % 10000)
            case 8:
                region = flag // 10000
            case _:
                raise ValueError("Invalid flag length!")
        flag_id = flag % 10000
        region_str = REGION_MAP.get(region)
        if region_str is None:
            region_str = f"Unknown Region {get_str_region(region)}"
            self.new_regions[region] = region_str
        flag_purpose = self._region_flag_helper(flag_id)
        return f"{region_str} | {flag_purpose}"
    
    def _get_representation(self, flag: int, created_at: int, val: bool = False):
        event_flag = self.flags.get(flag)
        if event_flag is not None:
            return event_flag.add_temp_info(created_at, val)
        flag_len = get_int_len(flag)
        match flag_len:
            case 8 | 10:
                event_flag = EventFlag(flag, self._map_region_flag(flag, flag_len), "Region", "", created_at, val)
            case 0 | 1 | 2 | 3 | 4:
                event_flag = EventFlag(flag, "Unknown system flag", "System", "", created_at, val)
            case _:
                event_flag = EventFlag(flag, "Unknown flag", "Unknown", "",  created_at, val)
        return event_flag

    def display_deltas(self, deltas: list[EventDelta]):
        created_at = int(time.time() * 1000)
        name = screenshot_name(created_at)
        path = str(Path("tmp", "screenshots", name))
        make_small_screenshot_and_save(path)
        flags = []
        for delta in deltas:
            flag = self._get_representation(delta.event_id, created_at, delta.val)
            if flag is not None:
                flags.append(flag)
        change = DisplayedDeltaChange(created_at, path, flags)
        print(change)
        self.new_change_recorded.emit(change)

    def display_item_changes(self, deltas: list[HasItemDelta]):
        print(f"Item deltas changed: {len(deltas)}")
        print("\n".join(("Got: " if delta.val else "Lost: ") + self.item_dict.get(f"0x{delta.item_id:08X}", f"Unknown item (0x{delta.item_id:08X})") for delta in deltas))



    def receive_flag(self, event_flag: EventFlag):
        self.flags[event_flag.event_id] = event_flag

        

