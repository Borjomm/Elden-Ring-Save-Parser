import time
from datetime import datetime
from .app_state import AppStore
from app.parser.adapter import ParserAdapter, FileLockedError, ParserError
from app.infrastructure.settings_repository import SettingsRepository
from app.infrastructure.watcher_service import FileWatcherService

class SaveController:
    def __init__(self, store: AppStore, adapter: ParserAdapter, watcher: FileWatcherService, settings: SettingsRepository):
        self.store = store
        self.adapter = adapter
        self.watcher = watcher
        self.settings = settings
        
        # Connect the watcher to our internal handler
        self.watcher.file_changed.connect(self._on_file_modified)

    def open_new_file(self, filepath: str):
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
                file_watching_datetime = datetime.now()
            )
            
            # 4. Update the OS watcher to point to the new file
            self.watcher.set_path(filepath)
            self.watcher.start()
            
            # 5. Persist the path to settings
            self.settings.save_session(filepath, 0)
            self.select_character_slot(0)

        except ParserError as e:
            self.store.update_state(is_loading=False, last_error=str(e))

    def select_character_slot(self, index: int):
        """Action: User clicks a character in the dropdown."""
        path = self.store.state.current_path
        if not path:
            return

        self.store.update_state(is_loading=True)
        
        try:
            data = self.adapter.load_character(path, index)
            
            self.store.update_state(
                current_slot=index,
                current_character=data,
                is_loading=False,
                file_watching_datetime = datetime.now()
            )
            
            # Persist choice
            self.settings.save_session(path, index)

        except ParserError as e:
            self.store.update_state(is_loading=False, last_error=str(e))

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
        for i in range(retries):
            try:
                # Use the adapter to get fresh data
                data = self.adapter.load_character(path, slot)
                
                # Update state (UI will auto-refresh)
                self.store.update_state(current_character=data, last_error=None)
                return 
                
            except FileLockedError:
                # Wait 200ms and try again
                time.sleep(0.2)
            except ParserError as e:
                self.store.update_state(last_error=f"Auto-reload failed: {e}")
                break

    def load_last_session(self):
        """Action: Called on App Startup to restore previous state."""
        last_path = self.settings.get_last_path()
        last_slot = self.settings.get_last_slot()
        
        if last_path:
            self.open_new_file(last_path)
            if last_slot is not None:
                self.select_character_slot(last_slot)

    def open_recent(self, filepath: str, slot: int):
        self.open_new_file(filepath)
        self.select_character_slot(slot)
        

    def get_last_known_dir(self):
        return self.settings.get_last_path()