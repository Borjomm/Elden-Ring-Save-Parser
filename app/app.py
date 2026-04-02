import sys
import os
import sqlite3
import signal
import traceback
from PySide6.QtWidgets import QApplication

# Import our new architectural layers
from parser.adapter import ParserAdapter
from infrastructure.settings_repository import SettingsRepository
from infrastructure.watcher_service import FileWatcherService
from core.app_state import AppStore
from core.save_controller import SaveController
from new_main_window import MainWindow

class EldenApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.setStyle("Fusion")
        
        # 1. Setup Signal Handling & Exception Hooks
        sys.excepthook = self.exception_hook
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        self.aboutToQuit.connect(self.on_close)

        # 2. Initialize Infrastructure Layer (The "Workers")
        self.db_connection = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), 'gamedata.db')
        )
        self.parser = ParserAdapter()
        self.settings = SettingsRepository("YourName", "EldenChecklist")
        self.watcher = FileWatcherService()

        # 3. Initialize Application Layer (The "Brain")
        self.store = AppStore()
        self.controller = SaveController(
            store=self.store,
            adapter=self.parser,
            watcher=self.watcher,
            settings=self.settings
        )

        # 4. Initialize Presentation Layer (The "Face")
        # We pass the store and controller so the UI can listen and act
        self.window = MainWindow(self.store, self.controller, self.db_connection)
        self.window.show()

        # 5. Kick off the initial session load
        self.controller.load_last_session()

        sys.exit(self.exec())

    def handle_signal(self, sig, frame):
        print(f"Received signal {sig}, exiting...")
        self.quit()

    def exception_hook(self, exc_type, exc_value, exc_tb):
        traceback.print_exception(exc_type, exc_value, exc_tb)
        self.cleanup()
        sys.exit(1)

    def on_close(self):
        print("Closing application...")
        self.cleanup()

    def cleanup(self):
        """Centralized cleanup logic."""
        if hasattr(self, "watcher"):
            self.watcher.stop()
        
        if hasattr(self, "db_connection"):
            try:
                self.db_connection.commit()
                self.db_connection.close()
                print("Database closed safely.")
            except Exception as e:
                print(f"Error during DB cleanup: {e}")