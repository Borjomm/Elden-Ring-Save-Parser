import ctypes

# A base class to ensure all our structs use 1-byte packing,
# which is the equivalent of '#pragma pack(1)' in C.
class PackedStructure(ctypes.Structure):
    _pack_ = 1

class CCharacterSelection(PackedStructure):
    _fields_ = [
        ("characterName", ctypes.c_wchar * 16),
        ("level", ctypes.c_uint)
    ]

class CCharHeader(PackedStructure):
    _fields_ = [
        ("checksum", ctypes.c_char * 16),
        ("version", ctypes.c_int)
    ]

class CGaItemEntry(PackedStructure):
    _fields_ = [
        ("gaHandle", ctypes.c_uint),
        ("itemId", ctypes.c_uint),
        ("aowId", ctypes.c_uint)
    ]

class CPlayer(PackedStructure):
    _fields_ = [
        ("health", ctypes.c_uint),
        ("maxHealth", ctypes.c_uint),
        ("baseMaxHealth", ctypes.c_uint),
        ("FP", ctypes.c_uint),
        ("maxFP", ctypes.c_uint),
        ("baseMaxFP", ctypes.c_uint),
        ("SP", ctypes.c_uint),
        ("maxSP", ctypes.c_uint),
        ("baseMaxSP", ctypes.c_uint),
        ("vigor", ctypes.c_uint),
        ("mind", ctypes.c_uint),
        ("endurance", ctypes.c_uint),
        ("strength", ctypes.c_uint),
        ("dexterity", ctypes.c_uint),
        ("intelligence", ctypes.c_uint),
        ("faith", ctypes.c_uint),
        ("arcane", ctypes.c_uint),
        ("humanity", ctypes.c_uint),
        ("level", ctypes.c_uint),
        ("souls", ctypes.c_uint),
        ("soulMemory", ctypes.c_uint),
        ("characterType", ctypes.c_uint),
        ("characterName", ctypes.c_wchar * 16),
        ("gender", ctypes.c_ubyte),
        ("archeType", ctypes.c_ubyte),
        ("voiceType", ctypes.c_ubyte),
        ("gift", ctypes.c_ubyte),
        ("additionalTalismanSlotsCount", ctypes.c_ubyte),
        ("summonSpiritLevel", ctypes.c_ubyte),
        ("furlCallingFingerOn", ctypes.c_ubyte),
        ("matchmakingWeaponLevel", ctypes.c_ubyte),
        ("greatRuneOn", ctypes.c_ubyte),
        ("maxCrimsonFlaskCount", ctypes.c_ubyte),
        ("maxCeruleanFlaskCount", ctypes.c_ubyte),
        ("padding", ctypes.c_ubyte * 29)
    ]

class CEquippedItemsGaHandles(PackedStructure):
    _fields_ = [
        ("leftHand1", ctypes.c_uint),
        ("rightHand1", ctypes.c_uint),
        ("leftHand2", ctypes.c_uint),
        ("rightHand2", ctypes.c_uint),
        ("leftHand3", ctypes.c_uint),
        ("rightHand3", ctypes.c_uint),
        ("arrows1", ctypes.c_uint),
        ("bolts1", ctypes.c_uint),
        ("arrows2", ctypes.c_uint),
        ("bolts2", ctypes.c_uint),
        ("head", ctypes.c_uint),
        ("chest", ctypes.c_uint),
        ("arms", ctypes.c_uint),
        ("legs", ctypes.c_uint),
        ("talisman1", ctypes.c_uint),
        ("talisman2", ctypes.c_uint),
        ("talisman3", ctypes.c_uint),
        ("talisman4", ctypes.c_uint)

    ]

class CInventoryHeld(PackedStructure):
    _fields_ = [
        ("itemId", ctypes.c_uint),
        ("quantity", ctypes.c_uint)
    ]

class CCharacterData(PackedStructure):
    _fields_ = [
        ("characterSelection", CCharacterSelection * 10),
        ("characterHeader", CCharHeader),
        ("gaItemCount", ctypes.c_uint),
        ("gaItems", CGaItemEntry * 5120),
        ("player", CPlayer),
        ("equippedItemsGaHandles", CEquippedItemsGaHandles),
        ("commonItemInventoryCount", ctypes.c_uint),
        ("commonItemsInventory", CInventoryHeld * 2688),
        ("keyItemInventoryCount", ctypes.c_uint),
        ("keyItemsInventory", CInventoryHeld * 384),
        ("commonItemStorageCount", ctypes.c_uint),
        ("commonItemsStorage", CInventoryHeld * 1920),
        ("keyItemStorageCount", ctypes.c_uint),
        ("keyItemsStorage", CInventoryHeld * 128),
        ("allItemsCount", ctypes.c_uint),
        ("allItems", ctypes.c_uint * 7000),
        ("totalDeathsCount", ctypes.c_uint),
        ("eventFlags", ctypes.c_ubyte * 1833375),
        ("dlc", ctypes.c_ushort)
    ]

