from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# 
CREATOR = "Borjom"
APP = "EldenRingChecklist"
DEFAULT_PATH = "AppData/Roaming/EldenRing/76561198231946968"
MAIN_DB_PATH = "app/gamedata.db"
TEMP_DB_PATH = "tmp/event_processing.db"

# Region items
REGION_NAME = Qt.ItemDataRole.UserRole + 1

# Boss items
OFFSET = Qt.ItemDataRole.UserRole
REMEMBRANCE = Qt.ItemDataRole.UserRole + 1
DLC = Qt.ItemDataRole.UserRole + 2
LINK = Qt.ItemDataRole.UserRole + 3

# Colors
QT_GREEN = QColor(0, 100, 0, 150)
QT_RED = QColor(130, 0, 0, 150)
QT_YELLOW = QColor(160, 120, 0, 150)

# Inventory
MAX_COMMON_ITEMS_INVENTORY = 2688
MAX_KEY_ITEMS_INVENTORY = 384
MAX_COMMON_ITEMS_STORAGE = 1920
MAX_KEY_ITEMS_STORAGE = 128

# Flags
EVENT_POOL_SIZE = 1833375
GAME_LOADED_FLAG = 50

REGION_FLAGS = [
(0, 10, "Bonfire Flag"),
(50, 10, "Init Flag"),
(100, 30, "System Flag"),
(200, 300, "Character Flag (No reset)"),
(2200, 300, "Character Flag (Reset)"),
(500, 200, "Object Flag (No reset)"),
(1500, 200, "Object Flag (No reset"),
(2500, 200, "Object Flag (Reset)"),
(8500, 200, "Object Action Flag"),
(700, 100, "Talk Flag (No reset)"),
(2700, 100, "Talk Flag (Reset)"),
(800, 100, "Boss Flag (No reset)"),
(2800, 100, "Boss Flag (Reset)"),
(900, 100, "Test/Debug Flag"),
(2900, 100, "Test/Debug Flag")
]

REGION_MAP = {
1000: "Stormveil Castle",
1001: "Chapel of Anticipation",
1800: "Limgrave - Stranded Graveyard",
604136: "Limgrave - Coastal Cave Entrance",
604137: "Limgrave - Stormfoot Catacombs Entrance",
604233: "Weeping Peninsula - Tombsward, Weeping Evergaol, Tombsward Cave Entrance",
604236: "Limgrave - Church of Elleh",
604237: "Limgrave - Agheel Lake",
604238: "Stormhill - Warmaster's Shack, Stormgate",
604335: "Limgrave - Seaside Ruins",
604336: "Limgrave - Agheel Lake, Dragon-Burnt Ruins",
604337: "Limgrave - Agheel Lake North, Murkwater Cave Entrance",
604433: "Weeping Peninsula - Castle Morne Rampart, Ailing Village Outskirts",
604436: "Limgrave - Waypoint Ruins",
609900: "Unknown region"
}