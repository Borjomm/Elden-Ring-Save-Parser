from app.parser.models import CCharacterData
from app.data.consts import MAX_COMMON_ITEMS_INVENTORY, MAX_COMMON_ITEMS_STORAGE, MAX_KEY_ITEMS_INVENTORY, MAX_KEY_ITEMS_STORAGE

AFFINITY_MAP = {
    0: "",
    1: "Heavy",
    2: "Keen",
    3: "Quality",
    4: "Fire",
    5: "Flame Art",
    6: "Lightning",
    7: "Sacred",
    8: "Magic",
    9: "Cold",
    10: "Poison",
    11: "Blood",
    12: "Occult"
}

def extract_gahandle_id_set(struct: CCharacterData) -> set[int]:
    """
    STABLE: Aggregates all 4 inventory buffers.
    Ignores the game's 'Count' variable and scans the entire allocated block.
    """
    ids = set()
    
    # We ignore the count variables entirely and use the MAX capacities
    inventory_sources = [
        (struct.commonItemsInventory, MAX_COMMON_ITEMS_INVENTORY),
        (struct.keyItemsInventory,    MAX_KEY_ITEMS_INVENTORY),
        (struct.commonItemsStorage,   MAX_COMMON_ITEMS_STORAGE),
        (struct.keyItemsStorage,      MAX_KEY_ITEMS_STORAGE),
    ]

    for array, max_capacity in inventory_sources:
        # Scan every single slot in the block
        for i in range(max_capacity):
            item_id = array[i].gaHandle
            # 0 is an empty slot, 0xFFFFFFFF is a deleted/invalid slot
            if item_id != 0 and item_id != 0xFFFFFFFF:
                ids.add(item_id)
                
    return ids

def extract_item_id_set(struct: CCharacterData) -> set[int]:
    ids = set()
    count = struct.allItemsCount
    array = struct.allItems
    for i in range(count):
        if array[i] != 0 and array[i] != 0xFFFFFFFF:
                ids.add(array[i])
    return ids

def get_item_type(item_id: int) -> str:
        category_mask = item_id & 0xF0000000
        
        if category_mask == 0x00000000: return "Weapon/Shield"
        if category_mask == 0x10000000: return "Armor"
        if category_mask == 0x20000000: return "Talisman"
        if category_mask == 0x40000000: return "Good/KeyItem"
        if category_mask == 0x80000000: return "Ash of War"
        
        return "Unknown"

def form_weapon_name(id: int, item_dict: dict[int, str]) -> str:
    clean_id = id // 10000 * 10000
    category = id % 10000
    upgrade = category % 100
    parts = [AFFINITY_MAP.get(category // 100, "ENHANCED"), item_dict.get(clean_id, f"Unknown Weapon ({id})"), f"+{upgrade}" if 0 < upgrade <= 25 else ""]
    return " ".join(p for p in parts if p)

def get_item_name(id: int, item_dict: dict[int, str]) -> str:
    def is_weapon(item_id: int) -> bool:
        # 0xF0000000 isolates the top hex digit. 
        # If the result is 0, it's a Weapon or Shield.
        return (item_id & 0xF0000000) == 0x00000000
    
    if is_weapon(id):
        return form_weapon_name(id, item_dict)
    else:
        return item_dict.get(id, f"Unknown {get_item_type(id)} ({id})")
        

