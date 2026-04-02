import os
from PySide6.QtCore import QObject, Signal, QTimer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WatchdogHandler(FileSystemEventHandler):
    def __init__(self, target_file, on_change_callback):
        self.target_file = os.path.abspath(target_file)
        self.on_change_callback = on_change_callback

    def on_modified(self, event):
        if not event.is_directory and os.path.abspath(event.src_path) == self.target_file:
            self.on_change_callback()

class FileWatcherService(QObject):
    """
    Infrastructure layer service for file monitoring.
    Uses Watchdog for OS events and a QTimer for debouncing.
    """
    file_changed = Signal(str)
    _raw_file_changed = Signal()

    def __init__(self):
        super().__init__()
        self._observer = None
        self._target_path = None
        
        # This timer is the 'Debounce'. It waits for the file system to 
        # go quiet for 500ms before notifying the app.
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(500) 
        self._debounce_timer.timeout.connect(self._emit_change)

        self._raw_file_changed.connect(self._debounce_timer.start)

    def set_path(self, path: str):
        self.stop()
        self._target_path = path
        if path:
            self.start()

    def start(self):
        if not self._target_path or self._observer:
            return

        self._observer = Observer()
        handler = WatchdogHandler(self._target_path, self._on_watchdog_event)
        
        # Watch the directory containing the file
        watch_dir = os.path.dirname(self._target_path)
        self._observer.schedule(handler, watch_dir, recursive=False)
        self._observer.start()

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        self._debounce_timer.stop()

    def _on_watchdog_event(self):
        """Called by the Watchdog thread when any modification is detected."""
        # Reset the timer. As long as the game is still writing, 
        # this will keep getting reset.
        self._raw_file_changed.emit()

    def _emit_change(self):
        """Called only after 500ms of silence on the file."""
        if self._target_path:
            self.file_changed.emit(self._target_path)