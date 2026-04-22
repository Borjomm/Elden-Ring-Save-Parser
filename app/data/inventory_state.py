from app.parser.models import CCharacterData
from app.data.consts import MAX_COMMON_ITEMS_INVENTORY, MAX_COMMON_ITEMS_STORAGE, MAX_KEY_ITEMS_INVENTORY, MAX_KEY_ITEMS_STORAGE

def extract_item_id_set(struct: CCharacterData) -> set[int]:
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
            item_id = array[i].itemId
            # 0 is an empty slot, 0xFFFFFFFF is a deleted/invalid slot
            if item_id != 0 and item_id != 0xFFFFFFFF:
                ids.add(item_id)
                
    return ids