from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# 
CREATOR = "Borjom"
APP = "EldenRingChecklist"
DEFAULT_PATH = "AppData/Roaming/EldenRing/76561198231946968"

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

