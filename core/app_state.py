from dataclasses import dataclass, field, replace
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from parser.wrapper import CharacterData, CharacterSelection
from PySide6.QtCore import QObject, Signal
if TYPE_CHECKING:
    from new_main_window import MainWindow

@dataclass(frozen=True)  # 'frozen' makes it immutable, preventing accidental side-effects
class AppState:
    # File Info
    _start_datetime: datetime = field(default_factory=datetime.now)
    current_path: Optional[str] = None
    current_slot: Optional[int] = None
    current_datetime: Optional[datetime] = None
    last_datetime: Optional[datetime] = None
    file_watching_datetime: Optional[datetime] = None
    
    
    # Character Data
    available_characters: List[CharacterSelection] = field(default_factory=list)
    current_character: Optional[CharacterData] = None
    recent_files: list[tuple[str, int]] = field(default_factory=list)
    
    # App Status
    is_loading: bool = False
    last_error: Optional[str] = None
    is_watching: bool = False

    def __post_init__(self):
        if self.current_datetime is None:
            object.__setattr__(self, 'current_datetime', self._start_datetime)

    @property
    def has_save_loaded(self) -> bool:
        return self.current_path is not None

    @property
    def has_character_selected(self) -> bool:
        return self.current_character is not None
    
    def time_since_last_save(self) -> float:
        if self.current_datetime is None:
            return 0.0
        elif self.last_datetime is None:
            delta = self.current_datetime - self._start_datetime
        else:
            delta = self.current_datetime - self.last_datetime
        return delta.total_seconds()
    
    def time_since_start(self) -> float:
        if self.current_datetime is None:
            return 0.0
        return (self.current_datetime - self._start_datetime).total_seconds()
    
    def time_since_watching(self) -> float:
        if self.current_datetime is None or self.file_watching_datetime is None:
            return 0.0
        return (self.current_datetime - self.file_watching_datetime).total_seconds()

class AppStore(QObject):
    """The container that holds the AppState and notifies the UI of changes."""
    state_changed = Signal(object)  # Emits the new AppState

    def __init__(self):
        super().__init__()
        self._state = AppState()

    @property
    def state(self) -> AppState:
        return self._state

    def update_state(self, **kwargs):
        """Updates the state using keyword arguments and notifies listeners."""
        self._state = replace(self._state, current_datetime = datetime.now(), last_datetime = self._state.current_datetime, **kwargs)
        self.state_changed.emit(self._state)