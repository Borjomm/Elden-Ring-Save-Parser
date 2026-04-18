from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QMenuBar
from sqlite3 import Connection
from functools import partial

from app.widgets.file_io_widget import FileIOWidget
from app.widgets.boss_tree import BossWindow
from app.widgets.graces_tree import GraceWindow
from app.widgets.event_editor import EventEditor
from app.util import utils
from app.core.app_state import AppStore, AppState, EventBus, DataSource
from app.core.save_controller import SaveController

class MainWindow(QMainWindow):
    def __init__(self, store: AppStore, controller: SaveController, db_conn: Connection, dispatcher: EventBus):
        super().__init__()
        self.store = store
        self.controller = controller
        self.db_conn = db_conn # Passed to Checklist tabs later
        self.dispatcher = dispatcher
        self._last_recent_list = self.controller.settings.get_recent_list()
        
        self.setWindowTitle("Elden Ring Save Inspector")
        self.setGeometry(*utils.get_spawn_coordinates(1920, 1080))

        # 1. Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 1.5 Menu

        # 2. File Selection Area (Top)
        # We pass the controller so it can trigger "Open File"
        self.file_header = FileIOWidget(self, self.controller, self.store, self.toggle_live_mode)
        layout.addWidget(self.file_header)

        # 3. Content Tabs
        self.tabs = QTabWidget()
        # self.stats_tab = StatsTab(self.store)
        # self.checklist_tab = ChecklistTab(self.store, self.db_conn)
        # self.tabs.addTab(self.stats_tab, "Stats")
        layout.addWidget(self.tabs)
        self.boss_tab = BossWindow(self.db_conn, self.store, self.dispatcher)
        self.tabs.addTab(self.boss_tab, "Bosses")
        self.grace_tab = GraceWindow(self.db_conn, self.store, self.dispatcher)
        self.tabs.addTab(self.grace_tab, "Graces")
        self.event_editor_tab = EventEditor(self.db_conn, self.controller)
        self.tabs.addTab(self.event_editor_tab, "Events")

        self._make_menu()

        # 4. Status Bar (To show errors or loading states)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 5. Connect to the Store to react to changes
        self.store.state_changed.connect(self.on_state_changed)

    def toggle_live_mode(self, enabled: bool):
        if self.controller.toggle_live_mode(enabled):
            self.file_header.toggle(not enabled)
            self.load_recent.setEnabled(not enabled)

    def on_state_changed(self, state: AppState):
        """The UI 'paints' itself based on the current AppState."""
        
        # Update File Widget
        self.file_header.update_from_state(state)

        if state.recent_files != self._last_recent_list:
            self._last_recent_list = state.recent_files
            self._regenerate_recent_menu()
        
        # Update Status Bar
        if state.attach_failed:
            err_msg = state.last_error
            self.file_header.live_checkbox.setChecked(False)
            if err_msg:
                self.status_bar.showMessage(err_msg)
        elif state.last_error:
            self.status_bar.showMessage(f"Error: {state.last_error}")
        elif state.data_source == DataSource.LIVE_MEMORY:
            self.status_bar.showMessage(f"Watching: Elden Ring memory")
        elif state.current_path and state.data_source == DataSource.SAVE_FILE:
            self.status_bar.showMessage(f"Watching: {state.current_path}")
        else:   
            self.status_bar.showMessage("Ready. Please select a save file.")

    def _clear_tmp_directory(self):
        self.event_editor_tab.temp_db_init = False
        utils.regenerate_temp()

    def _make_menu(self):
 
        self.menu = QMenuBar()
        self.file_menu = self.menu.addMenu("File")
        self.load_recent = self.file_menu.addMenu("Load Recent")
        self._regenerate_recent_menu()
        exit_action = utils.make_action(self, "Exit", self.close, "Ctrl+Q")
        self.file_menu.addAction(exit_action)

        self.tool_menu = self.menu.addMenu("Tools")
        event_tracker_toggle = utils.make_action(self, "Toggle event logging", self.controller.settings.set_event_logging)
        event_tracker_toggle.setCheckable(True)
        event_tracker_toggle.setChecked(self.controller.settings.get_event_logging())
        event_tracker_save = utils.make_action(self, "Save logged events to database", self.event_editor_tab.save_session_to_temp_db)
        event_tracker_regen_temp = utils.make_action(self, "Clear 'tmp' directory", self._clear_tmp_directory)
        self.tool_menu.addAction(event_tracker_toggle)
        self.tool_menu.addAction(event_tracker_save)
        self.tool_menu.addAction(event_tracker_regen_temp)

        self.setMenuBar(self.menu)

    def _regenerate_recent_menu(self):
        self.load_recent.clear()
        if not self._last_recent_list:
            self.load_recent.addAction("No recent files").setEnabled(False)
            return
        
        for p, s in self._last_recent_list:
            action = utils.make_action(self, p, partial(self.controller.open_recent, p, s))
            self.load_recent.addAction(action)


