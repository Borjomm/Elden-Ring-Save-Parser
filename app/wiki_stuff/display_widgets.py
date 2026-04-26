from pathlib import Path

from PySide6.QtWidgets import QWidget, QHBoxLayout, QTreeView, QFileSystemModel
from PySide6.QtCore import Qt
import frontmatter # using python-frontmatter

from app.wiki_stuff.wiki_engine import EldenWikiEngine
from app.wiki_stuff.debug_viewer import WikiDebugViewer

class WikiEditor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.addWidget

class DebugView(QWidget):
    def __init__(self, workspace_path: Path):
        super().__init__()
        self.workspace = workspace_path
        
        # Left Side: File Explorer
        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setRootPath(str(workspace_path))
        self.model.setNameFilters(["*.md"])
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(workspace_path)))
        
        # Open file on double click
        self.tree.doubleClicked.connect(self.on_file_double_clicked)
        
        # Right Side: Your Flag Menu + HTML Viewer (from earlier)
        self.viewer = WikiDebugViewer(workspace_path)
        
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
        clean_target = target_name.replace("public/", "")
        
        # 2. Look for the file on the hard drive
        matches = list(self.workspace.rglob(f"{clean_target}.md"))
        
        if matches:
            # 3. Get the OS path of the first match
            target_path = matches[0]
            
            # 4. Tell the tree to highlight it (optional but nice)
            idx = self.model.index(str(target_path))
            self.tree.setCurrentIndex(idx)
            
            # 5. Load it into the viewer
            self.viewer.load_page(target_path)
        else:
            print(f"Debug: File {clean_target}.md not found in {self.workspace}")


