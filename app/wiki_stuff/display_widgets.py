from pathlib import Path

from PySide6.QtWidgets import QWidget, QHBoxLayout, QTreeView, QFileSystemModel

from app.wiki_stuff.debug_viewer import WikiDebugViewer
from app.infrastructure.settings_dialog import WikiSettingsContainer

class WikiEditor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.addWidget

class DebugView(QWidget):
    def __init__(self, settings: WikiSettingsContainer):
        super().__init__()
        self.settings = settings
        self.workspace = Path(settings.root_path, settings.parse_path)
        
        # Left Side: File Explorer
        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath(self.workspace.as_posix())
        self.model.setNameFilters(["*.md"])
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.workspace.as_posix()))
        
        # Open file on double click
        self.tree.doubleClicked.connect(self.on_file_double_clicked)
        
        # Right Side: Your Flag Menu + HTML Viewer (from earlier)
        self.viewer = WikiDebugViewer(self.workspace)
        
        layout = QHBoxLayout(self)
        layout.addWidget(self.tree, 1)
        layout.addWidget(self.viewer, 3)

    def on_file_double_clicked(self, index):
        filepath = self.model.filePath(index)
        
        # 1. Read from Disk
        filepath = Path(self.model.filePath(index))
        if filepath.is_file():
            self.viewer.load_page(filepath)

    # --- How to handle [[Wikilinks]] without a DB! ---
    def handle_internal_link(self, target_name):
        """The callback for [[Wikilinks]] - searches the disk."""
        # 1. Strip 'public/' if it's there (as we discussed)
        if self.settings.parse_path:
            target_name = target_name.replace(self.settings.parse_path, "")
        
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


