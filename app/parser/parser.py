import ctypes
import os

from .models import CCharacterData
from .wrapper import CharacterData, CharacterSelection

_DLL_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "parser.dll")
try:
    _parser_lib = ctypes.CDLL(_DLL_PATH)
except OSError as e:
    raise ImportError(f"Could not load the C parser library at '{_DLL_PATH}'. Please ensure it is compiled and in the correct location. Error: {e}")

_update_data_func = _parser_lib.update_character_data
_update_data_func.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
_update_data_func.restype = ctypes.c_int

_get_ptr_func = _parser_lib.get_character_data_ptr
_get_ptr_func.restype = ctypes.POINTER(CCharacterData)

_invalidate_headers_func = _parser_lib.invalidate_headers
_invalidate_headers_func.restype = None

INITIALIZED_HEADERS = False
INITIALIZED = False

def update_data(filepath: str, character_slot: int, header_mode: bool) -> int:
    global INITIALIZED, INITIALIZED_HEADERS
    result = _update_data_func(filepath.encode(encoding="utf-8"), character_slot, header_mode)
    if result == 1:
        INITIALIZED_HEADERS = True
    elif result == 0:
        INITIALIZED_HEADERS = True
        INITIALIZED = True
    return result
    

def get_data() -> CharacterData:
    if INITIALIZED:
        return CharacterData(_get_ptr_func().contents)
    raise MemoryError("Data is not initialized")

def get_headers() -> list[CharacterSelection]:
    if INITIALIZED_HEADERS:
        return [CharacterSelection(_get_ptr_func().contents.characterSelection[i]) for i in range(10)]
    raise MemoryError("Headers are not initialized")

def invalidate() -> None:
    _invalidate_headers_func()

