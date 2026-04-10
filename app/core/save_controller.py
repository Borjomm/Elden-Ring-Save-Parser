import time
from datetime import datetime
from .app_state import AppStore, UpdateType
from app.parser.adapter import ParserAdapter, FileLockedError, ParserError
from app.infrastructure.settings_repository import SettingsRepository
from app.infrastructure.watcher_service import FileWatcherService
from app.infrastructure.live_watcher import LiveWatcherService

class SaveController:
    def __init__(self, store: AppStore, adapter: ParserAdapter, file_watcher: FileWatcherService, settings: SettingsRepository):
        self.store = store
        self.adapter = adapter
        self.file_watcher = file_watcher
        self.settings = settings
        
        # Connect the watcher to our internal handler
        self.file_watcher.file_changed.connect(self._on_file_modified)

    def open_new_file(self, filepath: str, slot: int = 0, startup: bool = False):
        """Action: User manually selects a new .sl2 file."""
        self.store.update_state(is_loading=True, last_error=None)
        
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
                is_loading=False,
                recent_files=self.settings.get_recent_list(),
                update_type = UpdateType.NONE
            )
            
            # 4. Update the OS watcher to point to the new file
            self.file_watcher.set_path(filepath)
            self.file_watcher.start()
            
            # 5. Persist the path to settings
            self.settings.save_session(filepath, 0)
            self.select_character_slot(slot, startup)

        except ParserError as e:
            self.store.update_state(is_loading=False, last_error=str(e), update_type = UpdateType.NONE)

    def select_character_slot(self, index: int, startup: bool = False):
        """Action: User clicks a character in the dropdown."""
        path = self.store.state.current_path
        if not path:
            return

        self.store.update_state(is_loading=True)
        
        try:
            data = self.adapter.load_character(path, index)
            
            self.store.update_state(
                current_slot=index,
                previous_character=None,
                current_character=data,
                is_loading=False,
                update_type = UpdateType.STARTUP if startup else UpdateType.MAJOR
            )
            
            # Persist choice
            self.settings.save_session(path, index)

            self.store.update_state(update_type = UpdateType.NONE)

        except ParserError as e:
            self.store.update_state(is_loading=False, last_error=str(e), update_type = UpdateType.NONE)

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
                self.store.update_state(last_character = self.store.state.current_character, current_character=data, last_error=None, update_type = UpdateType.MINOR)
                self.store.update_state(update_type = UpdateType.NONE)
                return 
                
            except FileLockedError:
                # Wait 200ms and try again
                time.sleep(0.2)
            except ParserError as e:
                self.store.update_state(last_error=f"Auto-reload failed: {e}", update_type = UpdateType.NONE)
                break

    def load_last_session(self):
        """Action: Called on App Startup to restore previous state."""
        last_path = self.settings.get_last_path()
        last_slot = self.settings.get_last_slot()
        
        if last_path:
            self.open_new_file(last_path, last_slot if last_slot is not None else 0, startup = True)

    def open_recent(self, filepath: str, slot: int):
        self.open_new_file(filepath, slot)
        

    def get_last_known_dir(self):
        return self.settings.get_last_path()