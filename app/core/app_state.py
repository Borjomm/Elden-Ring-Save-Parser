from dataclasses import dataclass, field, replace
from typing import Optional, List, Callable
from enum import Enum, auto
from PySide6.QtCore import QObject, Signal

from app.parser.wrapper import CharacterData, CharacterSelection
from app.data.containers import EventDelta, HasItemDelta

class DataSource(Enum):
    NONE = auto()
    SAVE_FILE = auto()
    LIVE_MEMORY = auto()

class UpdateType(Enum):
    NONE = auto()
    STARTUP = auto()
    MAJOR = auto()
    MINOR = auto()

class MemoryViewStatus(Enum):
    NONE = auto()
    MENU = auto()
    IN_GAME = auto()

@dataclass(frozen=True)  # 'frozen' makes it immutable, preventing accidental side-effects
class AppState:
    # File Info
    current_path: Optional[str] = None
    current_slot: Optional[int] = None
    
    
    # Character Data
    available_characters: List[CharacterSelection] = field(default_factory=list)
    previous_character: Optional[CharacterData] = None
    current_character: Optional[CharacterData] = None
    recent_files: list[tuple[str, int]] = field(default_factory=list)
    
    
    # App Status
    update_type: UpdateType = UpdateType.NONE
    data_source: DataSource = DataSource.NONE
    memory_view_status: MemoryViewStatus = MemoryViewStatus.NONE
    last_error: Optional[str] = None
    attach_failed: bool = False

    @property
    def has_save_loaded(self) -> bool:
        return self.current_path is not None

    @property
    def has_character_selected(self) -> bool:
        return self.current_character is not None

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
        self._state = replace(self._state, **kwargs)
        self.state_changed.emit(self._state)

class EventBus(QObject):
    cycle_finished = Signal()

    def __init__(self):
        super().__init__()
        self._subscribers: dict[int, list[Callable]] = {}
        self._wiki_event_subs: dict[int, list[Callable]] = {}
        self._wiki_item_subs: dict[int, list[Callable]] = {}
    
    def subscribe(self, event_id: int, callback: Callable):
        """Register a callback for a specific ID."""
        if event_id not in self._subscribers:
            self._subscribers[event_id] = []
        self._subscribers[event_id].append(callback)

    def subscribe_wiki(self, flag_dict: dict[str, list[int]], callback_event: Callable, callback_item: Callable):
        for val in flag_dict["events"]:
            if val not in self._wiki_event_subs:
                self._wiki_event_subs[val] = []
            self._wiki_event_subs[val].append(callback_event)
        for val in flag_dict["items"]:
            if val not in self._wiki_item_subs:
                self._wiki_item_subs[val] = []
            self._wiki_item_subs[val].append(callback_item)


    def dispatch_event_deltas(self, event_deltas: list[EventDelta], item_deltas: list[HasItemDelta]):
        for delta in event_deltas:
            # ONLY call the subscribers who care about this specific ID
            if delta.event_id in self._subscribers:
                for callback in self._subscribers[delta.event_id]:
                    callback(delta.val)
            if delta.event_id in self._wiki_event_subs:
                for callback in self._wiki_event_subs[delta.event_id]:
                    callback(delta)
        for delta in item_deltas:
            if delta.item_id in self._wiki_item_subs:
                for callback in self._wiki_item_subs[delta.item_id]:
                    callback(delta)

        self.cycle_finished.emit()
