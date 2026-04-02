from datetime import datetime
from PySide6.QtWidgets import QWidget

from app.core.app_state import AppStore, AppState

class BaseObserverTab(QWidget):
    def __init__(self, store: AppStore):
        super().__init__()
        self.store = store
        self._last_sync_time: datetime = datetime.min # When this tab last updated its UI
        
        # Every tab listens to the same signal
        self.store.state_changed.connect(self.on_state_updated)

    def on_state_updated(self, state: AppState):
        """Called whenever the AppState changes."""
        # 1. If we are currently visible, update immediately
        if self.isVisible():
            self._perform_sync(state)
        # 2. If hidden, we do nothing. The 'sync time' will naturally 
        # be behind the state's 'current_datetime'.

    def showEvent(self, event):
        """Called by Qt automatically when the tab becomes visible."""
        super().showEvent(event)
        # When the user clicks this tab, check if we are behind the state
        state = self.store.state
        if state.current_datetime and state.current_datetime > self._last_sync_time:
            print(f"Lazy Loading: Syncing {self.__class__.__name__}...")
            self._perform_sync(state)

    def _perform_sync(self, state: AppState):
        """Overridden by specific tabs (BossWindow, QuestWindow, etc.)"""
        if not state.current_character:
            return
            
        # Update the UI (your 'update_with' logic)
        self.sync_ui_data(state)
        
        # Update our local clock so we know we are current
        self._last_sync_time = state.current_datetime # pyright: ignore[reportAttributeAccessIssue]

    def sync_ui_data(self, state: AppState):
        raise NotImplementedError("Subclasses must implement sync_ui_data")