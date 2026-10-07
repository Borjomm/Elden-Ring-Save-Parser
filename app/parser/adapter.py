import ctypes
import threading

from app.parser.models import CCharacterData
from app.parser.wrapper import CharacterData, CharacterSelection
from app.data.consts import LIVE_MEMORY_DLL_PATH, SAVEFILE_DLL_PATH

from app.data.consts import EVENT_POOL_SIZE
from app.parser.models import CCharacterData, CEventDelta
from app.parser.wrapper import CharacterData

class ParserError(Exception):
    ...

class FileLockedError(ParserError):
    ...

class ParserAdapter:
    def __init__(self):
        self._lock = threading.RLock()
        self.parsed = False
        self._current_filepath = None

        self._init_savefile_dll()
        self._init_live_dll()

        self.__temp = CCharacterData()
        self._present = CCharacterData()
        self._past = CCharacterData()
        
        
    def _init_savefile_dll(self):
        try:
            _parser_lib = ctypes.CDLL(SAVEFILE_DLL_PATH)
        except OSError as e:
            raise ImportError(f"Could not load the C parser library at '{SAVEFILE_DLL_PATH}'. Please ensure it is compiled and in the correct location. Error: {e}")
        self._update_data_func = _parser_lib.update_character_data
        self._update_data_func.argtypes = [ctypes.POINTER(CCharacterData), ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
        self._update_data_func.restype = ctypes.c_int

        self._invalidate_headers_func = _parser_lib.invalidate_headers
        self._invalidate_headers_func.restype = None

    def _init_live_dll(self):
        try:
            self._live_lib = ctypes.CDLL(LIVE_MEMORY_DLL_PATH)
        except OSError as e:
            raise ImportError(f"Could not load the C parser library at '{LIVE_MEMORY_DLL_PATH}'. Please ensure it is compiled and in the correct location. Error: {e}")
        self.live_initialized = False
        self._live_lib.init.restype = ctypes.c_bool
        self._live_lib.close.restype = None
        self._live_lib.parse_character_data.argtypes = [ctypes.POINTER(CCharacterData)]
        self._live_lib.parse_character_data.restype = ctypes.c_bool
        self._live_lib.get_deltas_avx.argtypes = [ctypes.POINTER(CEventDelta), ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
        self._live_lib.get_deltas_avx.restype = ctypes.c_int

    def _update_data_save(self, filepath: str, character_slot: int, header_mode: bool = False) -> None:
        result = self._update_data_func(ctypes.byref(self.__temp), filepath.encode(), character_slot, header_mode)
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
    
    def load_headers_save(self, filepath: str) -> list[CharacterSelection]:
        with self._lock:
            if filepath != self._current_filepath:
                self._invalidate_headers_func()
                self._current_filepath = filepath

            self._update_data_save(filepath, 0, True)
            return [CharacterSelection(self.__temp.characterSelection[i]) for i in range(10)]
        
    def load_character_save(self, filepath: str, character_slot: int) -> CharacterData:
        with self._lock:
            if filepath != self._current_filepath:
                self._invalidate_headers_func()
                self._current_filepath = filepath

            self._update_data_save(filepath, character_slot, False)
            return self.update_cache(CCharacterData.from_buffer_copy(self.__temp))

    def init_live(self) -> bool:
        self.live_initialized = self._live_lib.init()
        return self.live_initialized

    def close_live(self) -> None:
        self._live_lib.close()
        self.live_initialized = False

    def parse_character_data_live(self) -> CharacterData:
        with self._lock:
            if not self.live_initialized:
                result = self.init_live()
                if not result:
                    raise ParserError(f"Unable to initialize {LIVE_MEMORY_DLL_PATH}")
            
            success = self._live_lib.parse_character_data(ctypes.byref(self.__temp))
            if success:
                return self.update_cache(CCharacterData.from_buffer_copy(self.__temp))
            else:
                self.close_live()
                raise ParserError(f"Unable to read Elden Ring memory")

    def update_cache(self, new_data: CCharacterData):
        ctypes.memmove(ctypes.byref(self._past), ctypes.byref(self._present), ctypes.sizeof(CCharacterData))
        self._present = new_data
        self.parsed = True
        return CharacterData(new_data)

    def parse_deltas(self, delta_container: ctypes.Array[CEventDelta], num_deltas: int) -> int:
        """Returns the size of the delta array"""
        return self._live_lib.get_deltas_avx(delta_container, num_deltas, self._present.eventFlags, self._past.eventFlags, EVENT_POOL_SIZE)

    def get_present_past_containers(self) -> tuple[CCharacterData, CCharacterData]:
        if not self.parsed:
            raise ParserError("Live memory not parsed")
        return self._present, self._past




