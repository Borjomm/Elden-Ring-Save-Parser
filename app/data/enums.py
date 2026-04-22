from enum import Enum, auto

class EventPosition(Enum):
    OLD = auto()
    NEW = auto()

class InventoryType(Enum):
    COMMON_INVENTORY = auto()
    COMMON_STORAGE = auto()
    KEY_INVENTORY = auto()
    KEY_STORAGE = auto()