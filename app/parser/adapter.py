import ctypes
import os
import threading

from app.parser.models import CCharacterData
from app.parser.wrapper import CharacterData, CharacterSelection

_DLL_PATH =  os.path.join(os.path.dirname(os.path.abspath(__file__)), "parser.dll")

class ParserError(Exception):
    ...

class FileLockedError(ParserError):
    ...

class ParserAdapter:
    def __init__(self):
        self._lock = threading.RLock()
        self._current_filepath = None
        self._load_dll()
        
    def _load_dll(self):
        try:
            _parser_lib = ctypes.CDLL(_DLL_PATH)
        except OSError as e:
            raise ImportError(f"Could not load the C parser library at '{_DLL_PATH}'. Please ensure it is compiled and in the correct location. Error: {e}")
        self._update_data_func = _parser_lib.update_character_data
        self._update_data_func.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        self._update_data_func.restype = ctypes.c_int

        self._get_ptr_func = _parser_lib.get_character_data_ptr
        self._get_ptr_func.restype = ctypes.POINTER(CCharacterData)

        self._invalidate_headers_func = _parser_lib.invalidate_headers
        self._invalidate_headers_func.restype = None

    def _update_data(self, filepath: str, character_slot: int, header_mode: bool) -> None:
        result = self._update_data_func(filepath.encode(), character_slot, header_mode)
        match result:
            case -1:
                raise FileLockedError("The file exists but cannot be opened (likely locked by Elden Ring)")
            case -2:
                raise ParserError("The file was opened, but the size or header is wrong")
            case -3:
                raise ParserError("The C library failed to allocate memory")
            case 0 | 1:
                return
            case _:
                raise ParserError(f"Unknown C error: {result}")
    
    def load_headers(self, filepath: str) -> list[CharacterSelection]:
        with self._lock:
            if filepath != self._current_filepath:
                self._invalidate_headers_func()
                self._current_filepath = filepath

            self._update_data(filepath, 0, True)
            contents = self._get_ptr_func().contents
            return [CharacterSelection(contents.characterSelection[i]) for i in range(10)]
        
    def load_character(self, filepath: str, character_slot: int) -> CharacterData:
        with self._lock:
            if filepath != self._current_filepath:
                self._invalidate_headers_func()
                self._current_filepath = filepath

            self._update_data(filepath, character_slot, False)
            ptr = self._get_ptr_func()
            snapshot = CCharacterData.from_buffer_copy(ptr.contents)
            return CharacterData(snapshot)




