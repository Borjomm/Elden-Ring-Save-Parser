import time
from .app_state import AppStore, UpdateType, DataSource, EventBus, MemoryViewStatus
from app.parser.adapter import ParserAdapter, FileLockedError, ParserError
from app.infrastructure.settings_repository import SettingsRepository
from app.infrastructure.watcher_service import FileWatcherService
from app.infrastructure.event_tracker import EventTracker
from app.parser.live_watcher import LiveWatcherService
from app.data.containers import Delta
from app.data.consts import GAME_LOADED_FLAG

class SaveController:
    def __init__(self, store: AppStore, adapter: ParserAdapter, file_watcher: FileWatcherService, live_watcher: LiveWatcherService, settings: SettingsRepository, event_tracker: EventTracker, dispatcher: EventBus):
        self.store = store
        self.adapter = adapter
        self.file_watcher = file_watcher
        self.live_watcher = live_watcher
        self.settings = settings
        self.event_tracker = event_tracker
        self.dispatcher = dispatcher
        
        # Connect the watcher to our internal handler
        self.file_watcher.file_changed.connect(self._on_file_modified)
        self.live_watcher.delta_detected.connect(self._on_memory_modified)

    def toggle_live_mode(self, enabled: bool) -> bool:
        """Action: UI toggles the 'Live Mode' switch."""
        self.store.update_state(attach_failed=False)
        if enabled:
            # 1. Stop watching file
            self.file_watcher.stop()
            # 2. Try to attach to Elden Ring memory
            if self.live_watcher.start(self.make_memory_scan):
                self.store.update_state(data_source = DataSource.LIVE_MEMORY)
                self.make_memory_scan(major=True)
                return True
            else:
                self.store.update_state(last_error="Could not find Elden Ring process.", data_source = DataSource.NONE, attach_failed=True, memory_view_status=MemoryViewStatus.NONE)
                return False
        else:
            # 1. Stop memory timer
            self.live_watcher.stop()
            # 2. Resume watching file
            self.load_last_session(startup=False)
            
            return True

    def _on_memory_modified(self, delta_list: list[Delta]):
        """Trigger: The LiveWatcher detected changes in RAM."""
        state = self.store.state
        if not state.current_character:
            return

        # 1. Get the latest pool from the C buffer
        new_flags = self.live_watcher.get_current_flags_bytes()
        
        # 2. Create an updated CharacterData snapshot
        updated_data = state.current_character.clone_with_flags(new_flags)

        memory_status = updated_data.get_event_state(GAME_LOADED_FLAG)

        new_status = MemoryViewStatus.IN_GAME if memory_status else MemoryViewStatus.MENU

        if new_status == state.memory_view_status:
            self.store.update_state(
                previous_character=self.store.state.current_character,
                current_character=updated_data
            )
            if self.settings.get_event_logging():
                self.event_tracker.display_deltas(delta_list)
            self.dispatcher.dispatch_deltas(delta_list)
        else:
            print("[MEMORY VIEWER]", "SWITCHED TO", "GAME" if memory_status else "MENU")
            self.store.update_state(
                previous_character=None,
                current_character=updated_data,
                memory_view_status=new_status,
                update_type=UpdateType.MAJOR
            )
            self.store.update_state(update_type=UpdateType.NONE)




    def make_memory_scan(self, major: bool = False):
        state = self.store.state

        if not state.current_character or state.data_source != DataSource.LIVE_MEMORY:
            return
        try:
            self.live_watcher.check_for_changes(supress_signal=major)
            if major:
                updated_data = state.current_character.clone_with_flags(self.live_watcher.get_current_flags_bytes())
                memory_status = updated_data.get_event_state(GAME_LOADED_FLAG)
                print("[MEMORY VIEWER]", "LOADED IN GAME" if memory_status else "LOADED IN MENU")
                self.store.update_state(
                    previous_character=None,
                    current_character=updated_data,
                    update_type=UpdateType.MAJOR,
                    memory_view_status=MemoryViewStatus.IN_GAME if memory_status else MemoryViewStatus.MENU
                )
                self.store.update_state(update_type=UpdateType.NONE)
        except ParserError as e:
            self.store.update_state(
                last_error=str(e), update_type = UpdateType.NONE, data_source = DataSource.NONE, attach_failed=True, memory_view_status=MemoryViewStatus.NONE
            )


    def open_new_file(self, filepath: str, slot: int = 0, startup: bool = False):
        """Action: User manually selects a new .sl2 file."""
        self.store.update_state(last_error=None)
        
        try:
            # 1. Load the headers (Character slots)
            headers = self.adapter.load_headers(filepath)
            
            # 2. Filter out empty slots (optional, or keep all 10)
            # available = [h for h in headers if h.name]
            
            # 3. Update state with the new file info
            self.store.update_state(
                current_path=filepath,
                available_characters=headers,
                current_slot=None,
                current_character=None,
                recent_files=self.settings.get_recent_list(),
                update_type = UpdateType.NONE,
                data_source = DataSource.SAVE_FILE,
                memory_view_status=MemoryViewStatus.NONE
            )
            
            # 4. Update the OS watcher to point to the new file
            self.file_watcher.set_path(filepath)
            self.file_watcher.start()
            
            # 5. Persist the path to settings
            self.settings.save_session(filepath, 0)
            self.select_character_slot(slot, startup)

        except ParserError as e:
            self.store.update_state(last_error=str(e), update_type = UpdateType.NONE, data_source = DataSource.NONE)

    def select_character_slot(self, index: int, startup: bool = False):
        """Action: User clicks a character in the dropdown."""
        path = self.store.state.current_path
        if not path:
            return
        
        try:
            data = self.adapter.load_character(path, index)
            
            self.store.update_state(
                current_slot=index,
                previous_character=None,
                current_character=data,
                update_type = UpdateType.STARTUP if startup else UpdateType.MAJOR
            )
            
            # Persist choice
            self.settings.save_session(path, index)

            self.store.update_state(update_type = UpdateType.NONE)

        except ParserError as e:
            self.store.update_state(last_error=str(e), update_type = UpdateType.NONE, data_source = DataSource.NONE, attach_failed = True)

    def _on_file_modified(self, filepath: str):
        """Trigger: The FileWatcher detected a change on disk."""
        # Only reload if we actually have a slot selected
        from PySide6.QtCore import QTimer
        state = self.store.state
        if state.current_slot is None:
            return

        print(f"Auto-reload triggered for: {filepath}")
        QTimer.singleShot(0, lambda: self._reload_with_retry(filepath, state.current_slot)) # type: ignore
        

    def _reload_with_retry(self, path: str, slot: int, retries=5):
        """Internal: Elden Ring often locks the file while writing."""
        for _ in range(retries):
            try:
                # Use the adapter to get fresh data
                data = self.adapter.load_character(path, slot)
                
                # Update state (UI will auto-refresh)
                self.store.update_state(previous_character = self.store.state.current_character, current_character=data, last_error=None, update_type = UpdateType.MINOR)
                self.store.update_state(update_type = UpdateType.NONE)
                return 
                
            except FileLockedError:
                # Wait 200ms and try again
                time.sleep(0.2)
            except ParserError as e:
                self.store.update_state(last_error=f"Auto-reload failed: {e}", update_type = UpdateType.NONE)
                break

    def load_last_session(self, startup: bool = True):
        """Action: Called on App Startup to restore previous state."""
        last_path = self.settings.get_last_path()
        last_slot = self.settings.get_last_slot()
        
        if last_path:
            self.open_new_file(last_path, last_slot if last_slot is not None else 0, startup = startup)

    def open_recent(self, filepath: str, slot: int):
        self.open_new_file(filepath, slot)
        

    def get_last_known_dir(self):
        return self.settings.get_last_path()