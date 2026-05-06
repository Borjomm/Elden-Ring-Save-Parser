from pathlib import Path
import sqlite3

from PySide6.QtWidgets import QWidget, QHBoxLayout, QTreeView, QFileSystemModel, QLabel, QPushButton, QVBoxLayout

from app.wiki_stuff.debug_viewer import WikiDebugViewer
from app.infrastructure.settings_repository import SettingsRepository
from app.infrastructure.settings_dialog import WikiSettingsContainer
from app.infrastructure.event_tracker import EventTracker
from app.data.consts import MAIN_DB_PATH

class WikiEditor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.addWidget

class DebugView(QWidget):
    def __init__(self, settings: SettingsRepository, container: WikiSettingsContainer):
        super().__init__()
        self.conn = sqlite3.connect(MAIN_DB_PATH)
        self.settings = settings
        self.container = container
        self.workspace = Path(container.root_path, container.parse_path)
        self.tracker = EventTracker(self.conn)
        
        # Left Side: File Explorer
        self.button = QPushButton("Change workspace...")
        self.button.clicked.connect(self.replace_workspace)
        self.label = QLabel(self.workspace.as_posix())
        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath(self.workspace.as_posix())
        self.model.setNameFilters(["*.md"])
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.workspace.as_posix()))
        
        # Open file on double click
        self.tree.doubleClicked.connect(self.on_file_double_clicked)
        
        # Right Side: Your Flag Menu + HTML Viewer (from earlier)
        self.viewer = WikiDebugViewer(self.workspace, self.tracker)
        
        layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.button)
        left_layout.addWidget(self.label)
        left_layout.addWidget(self.tree)
        layout.addLayout(left_layout, 1)
        layout.addWidget(self.viewer, 3)

    def on_file_double_clicked(self, index):
        filepath = self.model.filePath(index)
        
        # 1. Read from Disk
        filepath = Path(self.model.filePath(index))
        if filepath.is_file():
            self.viewer.load_page(filepath)

    def replace_workspace(self):
        container = self.settings.prompt_wiki_settings()
        if container is None:
            return
        self.workspace = Path(container.root_path, container.parse_path)
        self.label.setText(self.workspace.as_posix())
        self.model.setRootPath(self.workspace.as_posix())
        self.tree.setRootIndex(self.model.index(self.workspace.as_posix()))
        new_viewer = WikiDebugViewer(self.workspace, self.tracker)
        self.layout().replaceWidget(self.viewer, new_viewer) # pyright: ignore[reportOptionalMemberAccess]
        self.viewer.deleteLater()
        self.viewer = new_viewer

    # --- How to handle [[Wikilinks]] without a DB! ---
    def handle_internal_link(self, target_name):
        """The callback for [[Wikilinks]] - searches the disk."""
        # 1. Strip 'public/' if it's there (as we discussed)
        if self.container.parse_path:
            target_name = target_name.replace(self.container.parse_path, "")
        
        # 2. Look for the file on the hard drive
        matches = list(self.workspace.rglob(f"{target_name}.md"))
        
        if matches:
            # 3. Get the OS path of the first match
            target_path = matches[0]
            
            # 4. Tell the tree to highlight it (optional but nice)
            idx = self.model.index(str(target_path))
            self.tree.setCurrentIndex(idx)
            
            # 5. Load it into the viewer
            self.viewer.load_page(target_path)
        else:
            print(f"Debug: File {target_name}.md not found in {self.workspace}")


