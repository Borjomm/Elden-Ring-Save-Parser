from .models import *
from app.data.block import PYTHON_BLOCK_MAP

class CharacterSelection:
    def __init__(self, c_struct: CCharacterSelection):
        self._struct = c_struct

    @property
    def name(self) -> str:
        return self._struct.characterName
    
    @property
    def level(self) -> int:
        return self._struct.level
    
    def __str__(self) -> str:
        return f"{self.name} - SL{self.level}"
    
class CharacterHeader:
    def __init__(self, c_struct: CCharHeader):
        self._struct = c_struct

    @property
    def checksum(self) -> bytes:
        return self._struct.checksum
    
    @property
    def version(self) -> int:
        return self._struct.version
    
    def __str__(self) -> str:
        return f"Version: {self.version}. Checksum - {self.checksum.hex()}"
    
class GaItemEntry:
    def __init__(self, c_struct: CGaItemEntry):
        self._struct = c_struct

    @property
    def ga_handle(self) -> int:
        return self._struct.gaHandle
    
    @property
    def item_id(self) -> int:
        return self._struct.itemId
    
    @property
    def ashes_id(self) -> int:
        return self._struct.aowId
    
    def __str__(self) -> str:
        return f"GA: {hex(self.ga_handle)}, ID: {hex(self.item_id)}{f', Ashes ID: {hex(self.ashes_id)}' if self.ashes_id else ''}"
    
class Player:
    def __init__(self, c_struct: CPlayer):
        self._struct = c_struct

    @property
    def health(self) -> int:
        return self._struct.health
    
    @property
    def max_health(self) -> int:
        return self._struct.maxHealth
    
    @property
    def base_max_health(self) -> int:
        return self._struct.baseMaxHealth
    
    @property
    def fp(self) -> int:
        return self._struct.FP
    
    @property
    def max_fp(self) -> int:
        return self._struct.maxFP
    
    @property
    def base_max_fp(self) -> int:
        return self._struct.baseMaxFP
    
    @property
    def sp(self) -> int:
        return self._struct.SP
    
    @property
    def max_sp(self) -> int:
        return self._struct.maxSP
    
    @property
    def base_max_sp(self) -> int:
        return self._struct.baseMaxSP
    
    @property
    def vigor(self) -> int:
        return self._struct.vigor
    
    @property
    def mind(self) -> int:
        return self._struct.mind
    
    @property
    def endurance(self) -> int:
        return self._struct.endurance
    
    @property
    def strength(self) -> int:
        return self._struct.strength
    
    @property
    def dexterity(self) -> int:
        return self._struct.dexterity
    
    @property
    def intelligence(self) -> int:
        return self._struct.intelligence
    
    @property
    def faith(self) -> int:
        return self._struct.faith
    
    @property
    def arcane(self) -> int:
        return self._struct.arcane
    
    @property
    def humanity(self) -> int:
        return self._struct.humanity
    
    @property
    def level(self) -> int:
        return self._struct.level
    
    @property
    def souls(self) -> int:
        return self._struct.souls
    
    @property
    def soul_memory(self) -> int:
        return self._struct.soulMemory
    
    @property
    def character_type(self) -> int:
        return self._struct.characterType
    
    @property
    def character_name(self) -> str:
        return self._struct.characterName
    
    @property
    def gender(self) -> int:
        return int(self._struct.gender)
    
    @property
    def arche_type(self) -> int:
        return int(self._struct.archeType)
    
    @property
    def voice_type(self) -> int:
        return int(self._struct.voiceType)
    
    @property
    def gift(self) -> int:
        return int(self._struct.gift)
    
    @property
    def talisman_slots(self) -> int:
        return int(self._struct.additionalTalismanSlotsCount) + 1
    
    @property
    def summon_spirit_level(self) -> int:
        return int(self._struct.summonSpiritLevel)
    
    @property
    def matchmaking_weapon_level(self) -> int:
        return int(self._struct.matchmakingWeaponLevel)
    
    @property
    def max_crimson_flask_count(self) -> int:
        return int(self._struct.maxCrimsonFlaskCount)
    
    @property
    def max_cerulean_flask_count(self) -> int:
        return int(self._struct.maxCeruleanFlaskCount)
    
    
    def furl_calling_finger_on(self) -> bool:
        return self._struct.furlCallingFingerOn != 0
    
    def great_rune_on(self) -> bool:
        return self._struct.greatRuneOn != 0
    
class EquippedItemHandles:
    def __init__(self, c_struct: CEquippedItemsGaHandles):
        self._struct = c_struct

    @property
    def lefthand1(self) -> int:
        return self._struct.leftHand1
    
    @property
    def lefthand2(self) -> int:
        return self._struct.leftHand2
    
    @property
    def lefthand3(self) -> int:
        return self._struct.leftHand3
    
    @property
    def righthand1(self) -> int:
        return self._struct.rightHand1
    
    @property
    def righthand2(self) -> int:
        return self._struct.rightHand2
    
    @property
    def righthand3(self) -> int:
        return self._struct.rightHand3
    
    @property
    def arrows1(self) -> int:
        return self._struct.arrows1
    
    @property
    def arrows2(self) -> int:
        return self._struct.arrows2
    
    @property
    def bolts1(self) -> int:
        return self._struct.bolts1
    
    @property
    def bolts2(self) -> int:
        return self._struct.bolts2
    
    @property
    def head(self) -> int:
        return self._struct.head
    
    @property
    def chest(self) -> int:
        return self._struct.chest
    
    @property
    def arms(self) -> int:
        return self._struct.arms
    
    @property
    def legs(self) -> int:
        return self._struct.legs
    
    @property
    def talisman1(self) -> int:
        return self._struct.talisman1
    
    @property
    def talisman2(self) -> int:
        return self._struct.talisman2
    
    @property
    def talisman3(self) -> int:
        return self._struct.talisman3
    
    @property
    def talisman4(self) -> int:
        return self._struct.talisman4
    
    @property
    def weapons(self) -> list[int]:
        return [self.righthand1, self.righthand2, self.righthand3, self.lefthand1, self.lefthand2, self.lefthand3]
    
    @property
    def projectiles(self) -> list[int]:
        return [self.arrows1, self.arrows2, self.bolts1, self.bolts2]
    
    @property
    def armor(self) -> list[int]:
        return [self.head, self.chest, self.arms, self.legs]
    
    @property
    def talismans(self) -> list[int]:
        return [self.talisman1, self.talisman2, self.talisman3, self.talisman4]
    
class InventoryItem:
    def __init__(self, c_struct: CInventoryHeld):
        self._struct = c_struct

    @property
    def item_id(self) -> int:
        return self._struct.itemId
    
    @property
    def quantity(self) -> int:
        return self._struct.quantity
    
class CharacterData:
    def __init__(self, c_struct: CCharacterData):
        self._struct = c_struct
        self._flags = bytes(c_struct.eventFlags)
        self._character_selections = {}
        self._player = None
        self._header = None
        self._ga_items_dict = None
        self._equipped_ga_handles = None
        self._item_set = set()


    @property
    def header(self) -> CharacterHeader:
        if not self._header:
            self._header = CharacterHeader(self._struct.characterHeader)
        return self._header
    
    @property
    def ga_item_count(self) -> int:
        return self._struct.gaItemCount
    
    @property
    def player(self) -> Player:
        if not self._player:
            self._player = Player(self._struct.player)
        return self._player
    
    @property
    def equipped_item_handles(self) -> EquippedItemHandles:
        if not self._equipped_ga_handles:
            self._equipped_ga_handles = EquippedItemHandles(self._struct.equippedItemsGaHandles)
        return self._equipped_ga_handles
    
    @property
    def common_inventory_count(self) -> int:
        return self._struct.commonItemInventoryCount
    
    @property
    def key_inventory_count(self) -> int:
        return self._struct.keyItemInventoryCount
    
    @property
    def common_storage_count(self) -> int:
        return self._struct.commonItemStorageCount
    
    @property
    def key_storage_count(self) -> int:
        return self._struct.keyItemStorageCount
    
    @property
    def all_items_count(self) -> int:
        return self._struct.allItemsCount
    
    @property
    def total_deaths_count(self) -> int:
        return self._struct.totalDeathsCount
    
    def get_character_info(self, index) -> CharacterSelection:
        if not 0 <= index < 10:
            raise ValueError("Invalid index while getting character")
        if index not in self._character_selections.keys():
            self._character_selections[index] = CharacterSelection(self._struct.characterSelection[index])
        return self._character_selections[index]
    
    def get_characters(self) -> list[CharacterSelection]:
        return [self.get_character_info(i) for i in range(10)]
    
    def get_event_state(self, event_id: int) -> bool:
        """Used during Major Updates by UI elements."""
        # 1. Python calculates the exact offset dynamically
        block_id = event_id // 1000
        remainder = event_id % 1000
        
        base_bit_offset = PYTHON_BLOCK_MAP.get(block_id)
        if base_bit_offset is None:
            return False
            
        byte_part = (remainder // 8) * 8
        bit_part = 7 - (remainder % 8)
        target_offset = base_bit_offset + byte_part + bit_part
        
        # 2. Grab the specific flag from the local buffer wrapper
        return self.get_flag(target_offset)
    
    def get_flag(self, bit_offset) -> bool:
        byte = self._flags[bit_offset // 8]
        bit = bit_offset % 8
        bit_mask = 1 << bit
        return bit_mask & byte != 0
    
    def has_dlc(self) -> bool:
        return self._struct.dlc != 0
    
    def check_item_set(self) -> None:
        if not self._item_set:
            self._item_set = {self._struct.allItems[i] for i in range(self.all_items_count)}
    
    def get_items(self) -> set[int]:
        self.check_item_set()
        return self._item_set
    
    def has_item(self, item_id: int) -> bool:
        self.check_item_set()
        return item_id in self._item_set
    
    def clone_with_flags(self, new_flag_bytes: bytes) -> 'CharacterData':
        """Creates a copy of the character data but with updated event flags."""
        # This keeps the name, level, and items the same, but swaps the flag buffer
        # Note: If you want to update HP/Souls too, you'd add that here
        import copy
        new_obj = copy.copy(self) 
        new_obj._flags = new_flag_bytes
        return new_obj
    
    