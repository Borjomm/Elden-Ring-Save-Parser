from PySide6.QtWidgets import QTreeView, QVBoxLayout, QWidget, QLineEdit, QHBoxLayout, QPushButton, QLabel, QMenu, QApplication
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Qt, QSortFilterProxyModel
from typing import cast
from sqlite3 import Connection
import json

from app.parser.wrapper import CharacterData
from app.data.consts import QT_GREEN, QT_RED, QT_YELLOW
from app.core.app_state import AppStore, AppState, UpdateType, EventBus
from app.util.utils import make_combo_widget
from app.util.animation import flash_item
from app.widgets.wiki_viewer import WikiViewer
from app.wiki_stuff.wiki_engine import EldenWikiEngine
from .tree_item import RegionItem, GraceItem, ExpandableItem, WikiItem
from .observer_tab import BaseObserverTab

class WikiWindow(BaseObserverTab):
    def __init__(self, connection: Connection, store: AppStore, dispatcher: EventBus):
        super().__init__(store)
        self.connection = connection
        self.dispatcher = dispatcher
        self.folders: dict[str, ExpandableItem] = {}
        self.items: dict[str, WikiItem] = {}
        self.setWindowTitle("Wiki")

        # Create the base model
        self.base_model = QStandardItemModel()

        # Create the filter proxy model
        self.proxy_model = WikiProxyModel()
        self.proxy_model.setSourceModel(self.base_model)

        self.tree = QTreeView()
        self.tree.setModel(self.proxy_model)
        self.tree.setUniformRowHeights(True)
        self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(self.on_item_double_clicked)

        self.viewer = WikiViewer(self.load_page_content)

        # Set up the tree view
        self.top_bar = QWidget()

        self.button_widget = QWidget()

        self.expand_button = QPushButton("Expand all")
        self.expand_button.pressed.connect(self.tree.expandAll)

        self.collapse_button = QPushButton("Collapse all")
        self.collapse_button.pressed.connect(self.tree.collapseAll)

        self.left_button_layout = QVBoxLayout()
        self.left_button_layout.addWidget(self.expand_button)
        self.left_button_layout.addWidget(self.collapse_button)
        self.button_widget.setLayout(self.left_button_layout)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")
        self.search.textChanged.connect(self.update_search_box)

        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(self.button_widget)
        self.top_layout.addWidget(self.search)
        self.top_bar.setLayout(self.top_layout)

        # Layout
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(self.top_bar)
        self.left_layout.addWidget(self.tree)

        layout = QHBoxLayout(self)
        layout.addLayout(self.left_layout)
        layout.addWidget(self.viewer)

        # Populate the model
        self.populate_model()

        # Context Menu
        #self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        #self.tree.customContextMenuRequested.connect(self.on_context_menu)

        # Resize columns
        self.tree.resizeColumnToContents(0)

    def update_with(self, data: CharacterData, state: AppState):
        self.base_model.blockSignals(True)
        
        is_startup = state.update_type == UpdateType.STARTUP
        self._full_sync(data, is_startup)

        self.base_model.blockSignals(False)
        self.tree.viewport().update()
        self.proxy_model.invalidate()

    def _full_sync(self, data: CharacterData, is_startup: bool):
        for item in self.items.values():
            item.load_flag_state(data, major=True)

    def update_search_box(self, text):
        if len(text) > 5:
            self.tree.expandAll()
        self.proxy_model.set_search_text(text)

    def _handle_minor_expansion(self, item: QStandardItem):
        """Logic to expand region if a grace is killed while folder is closed."""
        region_proxy_index = self.proxy_model.mapFromSource(item.index())
        if self.isVisible() and region_proxy_index.isValid() and not self.tree.isExpanded(region_proxy_index):
            self.tree.expand(region_proxy_index)

    def _handle_folders(self, folder_str: str) -> QStandardItem:
        item = self.base_model.invisibleRootItem()
        if not folder_str:
            return item
        path = ""
        for folder in folder_str.split("/"):
            path = f"{path}/{folder}" if path else folder
            if path in self.folders:
                item = self.folders[path]
                continue
            new_item = ExpandableItem(self._handle_minor_expansion, folder)
            self.folders[path] = new_item
            item.appendRow(new_item)
            item = new_item
        return item
    
    def load_page_content(self, target: str):
        cursor = self.connection.cursor()
        print(f"Accessing {target}...")

        # 1. Simple search: if it has a slash, check filepath. Else, check name.
        if "/" in target or target.endswith(".md"):
            # Append .md if Obsidian didn't include it in the link
            search_target = target if target.endswith(".md") else f"{target}.md"
            cursor.execute("""
                SELECT filepath, markdown, hidden_markdown 
                FROM wiki_entries 
                WHERE filepath = ? COLLATE NOCASE
            """, (search_target,))
        else:
            cursor.execute("""
                SELECT filepath, markdown, hidden_markdown 
                FROM wiki_entries 
                WHERE name = ? COLLATE NOCASE
            """, (target,))

        row = cursor.fetchone()

        # 2. Handle 404
        if not row:
            self.viewer.load_page(f"<h2 style='color:red;'>Not Found</h2><p>Could not find link: {target}</p>")
            return

        filepath, markdown_text, hidden_md = row

        # 3. Get the item's live state from your pre-built dictionary
        item = self.items.get(filepath)
        current_state = item.flag_state if item else {"events": {}, "items": {}}
        unlock_ids = item.unlock_ids if item else None

        # 4. Process and return HTML
        html_output = EldenWikiEngine.process(markdown_text, current_state, hidden_md, unlock_ids)
        self.viewer.load_page(html_output)
            
            

    def populate_model(self):
        query = "SELECT filepath, name, conditions, unlock_ids FROM wiki_entries ORDER BY filepath"
        cursor = self.connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        for filepath, name, conditions, unlock_ids in rows:
            folders, _, _ = filepath.rpartition("/")
            parent = self._handle_folders(folders)
            conditions = {key: [int(i) for i in value] for key, value in json.loads(conditions).items()}
            unlock_ids = [] if not unlock_ids else unlock_ids.split(",")
            item = WikiItem(self._handle_minor_expansion, self.dispatcher, name, filepath, conditions, unlock_ids)
            self.items[filepath] = item
            parent.appendRow(item)

    def sync_ui_data(self, state: AppState):
        """This only runs when visible or upon opening."""
        # This is your existing update_with logic
        if state.current_character:
            self.update_with(state.current_character, state)

    def on_item_double_clicked(self, proxy_index):
        if not proxy_index.isValid():
            return

        # 2. Map the View's proxy index to the Base Model's source index
        source_index = self.proxy_model.mapToSource(proxy_index)

        # 3. Grab the actual item from the base model
        item = self.base_model.itemFromIndex(source_index)

        if isinstance(item, WikiItem):
            self.load_page_content(item.filepath)
            

class WikiProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.search_text = ""

    def filterAcceptsRow(self, source_row, source_parent):
        model = cast(QStandardItemModel, self.sourceModel())
        index = model.index(source_row, 0, source_parent)
        item = model.itemFromIndex(index)

        
        if isinstance(item, WikiItem):
            if not item.isEnabled():
                return False
            if self.search_text:
                parent_item = item.parent()
                text = self.search_text.lower()
                if parent_item and text in parent_item.text().lower():
                    return True
                if text not in item.text().lower():
                    return False
        elif isinstance(item, ExpandableItem):
            for i in range(item.rowCount()):
                if self.filterAcceptsRow(i, index):
                    return True
            return False

        return True

    def set_search_text(self, text: str):
        self.search_text = text
        self.invalidateFilter()