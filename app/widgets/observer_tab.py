from datetime import datetime
from PySide6.QtWidgets import QWidget

from app.core.app_state import AppStore, AppState, UpdateType

class BaseObserverTab(QWidget):
    def __init__(self, store: AppStore):
        super().__init__()
        self.store = store
        self.dirty = True
        
        # Every tab listens to the same signal
        self.store.state_changed.connect(self.on_state_updated)

    def on_state_updated(self, state: AppState):
        """Called whenever the AppState changes."""
        # 1. If we are currently visible, update immediately
        if state.update_type == UpdateType.NONE: return
        if not state.current_character: return
        if self.isVisible():
            self._perform_sync(state)
        else:
            self.dirty = True
            print("Dirty")

    def showEvent(self, event):
        """Called by Qt automatically when the tab becomes visible."""
        super().showEvent(event)
        # When the user clicks this tab, check if we are behind the state
        if self.dirty:
            self._perform_sync(self.store.state)
            print("Clean")
            self.dirty = False

    def _perform_sync(self, state: AppState):
        """Overridden by specific tabs (BossWindow, QuestWindow, etc.)"""
        if not state.current_character:
            return
            
        # Update the UI (your 'update_with' logic)
        self.sync_ui_data(state)
        

    def sync_ui_data(self, state: AppState):
        raise NotImplementedError("Subclasses must implement sync_ui_data")