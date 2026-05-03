
from PySide6.QtWidgets import QTreeView, QVBoxLayout, QWidget, QLineEdit, QHBoxLayout, QPushButton, QLabel, QMenu, QApplication
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Qt, QSortFilterProxyModel
from typing import cast
from sqlite3 import Connection

from app.parser.wrapper import CharacterData
from app.data.consts import QT_GREEN, QT_RED, QT_YELLOW
from app.core.app_state import AppStore, AppState, UpdateType, EventBus
from app.util.utils import make_combo_widget
from app.util.animation import flash_item
from .tree_item import RegionItem, GraceItem
from .observer_tab import BaseObserverTab

class GraceWindow(BaseObserverTab):
    def __init__(self, connection: Connection, store: AppStore, dispatcher: EventBus):
        super().__init__(store)
        self.connection = connection
        self.dispatcher = dispatcher
        self.has_dlc = True
        self.setWindowTitle("Grace Tracker")

        # Create the base model
        self.base_model = QStandardItemModel()

        # Create the filter proxy model
        proxy_dlc_flag = None if self.has_dlc else 0
        self.proxy_model = BossFilterProxyModel(has_dlc=proxy_dlc_flag)
        self.proxy_model.setSourceModel(self.base_model)

        self.tree = QTreeView()
        self.tree.setModel(self.proxy_model)
        self.tree.setUniformRowHeights(True)
        self.tree.setHeaderHidden(True)

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

        self.dlc_box = make_combo_widget("DLC", ["Show all", "Don't show", "Only show"], self.proxy_model.set_show_dlc, not self.has_dlc)
        self.show_box = make_combo_widget("Filter selected", ["Show all", "Show checked", "Show unchecked"], self.proxy_model.set_show_checked_only, 0)

        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(self.button_widget)
        self.top_layout.addWidget(self.search)
        self.top_layout.addWidget(self.dlc_box)
        self.top_layout.addWidget(self.show_box)
        self.top_bar.setLayout(self.top_layout)

        # Bottom text
        self.bottom_text_bar = QLabel("")

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.top_bar)
        layout.addWidget(self.tree)
        layout.addWidget(self.bottom_text_bar)

        # Populate the model
        self.populate_model()
        self.update_all_region_counts()

        # Context Menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_context_menu)

        # Resize columns
        self.tree.resizeColumnToContents(0)

    def populate_model(self):
        self.event_flag_to_item = {}
        root_item = self.base_model.invisibleRootItem()
        region_items = {}

        query = "SELECT * FROM graces ORDER BY region_order, region, name"
        cursor = self.connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        self.base_model.layoutAboutToBeChanged.emit()
        for event_id, grace_name, region,  dlc, _ in rows:
            if region not in region_items and region:
                region_item = RegionItem(self._handle_minor_expansion, self.dispatcher, region)
                root_item.appendRow(region_item)
                region_items[region] = region_item
            if not region:
                parent_item = root_item
            else:
                parent_item = region_items[region]
            grace_item = GraceItem(
                ui_callback=self._handle_minor_expansion,
                dispatcher=self.dispatcher,
                grace_name=grace_name,
                event_id=event_id,
                dlc=dlc)

            self.event_flag_to_item[event_id] = grace_item

            parent_item.appendRow(grace_item)

        self.base_model.layoutChanged.emit()

    def update_all_region_counts(self):
        for i in range(self.base_model.rowCount()):
            region_item = self.base_model.item(i)
            if isinstance(region_item, RegionItem):
                region_item.update_count()


    def update_with(self, data: CharacterData, state: AppState):
        self.has_dlc = data.has_dlc()
        self.base_model.blockSignals(True)
        
        is_startup = state.update_type == UpdateType.STARTUP
        self._full_sync(data, is_startup)

        self.base_model.blockSignals(False)
        self.tree.viewport().update()
        self.proxy_model.invalidate()

    def _handle_minor_expansion(self, item: QStandardItem):
        """Logic to expand region if a grace is killed while folder is closed."""
        region_proxy_index = self.proxy_model.mapFromSource(item.index())
        if self.isVisible() and region_proxy_index.isValid() and not self.tree.isExpanded(region_proxy_index):
            self.tree.expand(region_proxy_index)

    def _handle_region_flash(self, region_item, added, removed):
        """Logic to flash the region item if it is currently collapsed."""
        if not added and not removed:
            return
        region_proxy_index = self.proxy_model.mapFromSource(region_item.index())
        if region_proxy_index.isValid() and not self.tree.isExpanded(region_proxy_index):
            if added and removed: color = QT_YELLOW
            elif added: color = QT_GREEN
            else: color = QT_RED
            flash_item(self.base_model, region_item.index(), color)

    def _full_sync(self, data: CharacterData, is_startup):
        root_item = self.base_model.invisibleRootItem()
        for i in range(root_item.rowCount()):
            region_grace_added = False
            region_grace_removed = False
            region_item = root_item.child(i)

            if isinstance(region_item, GraceItem): #TODO: Implement abstract logic
                new_val = data.get_event_state(region_item.event_id)
                new_state = Qt.CheckState.Checked if new_val else Qt.CheckState.Unchecked
                
                if region_item.checkState() != new_state:
                    region_item.setCheckState(new_state)
                    continue
            
            # (Check visibility/expanded state just like your original code)
            proxy_idx = self.proxy_model.mapFromSource(region_item.index())
            is_expanded = self.tree.isExpanded(proxy_idx) if proxy_idx.isValid() else True

            for j in range(region_item.rowCount()):
                grace_item = region_item.child(j)
                if not isinstance(grace_item, GraceItem): continue
                new_val = data.get_event_state(grace_item.event_id)
                new_state = Qt.CheckState.Checked if new_val else Qt.CheckState.Unchecked
                
                if grace_item.checkState() != new_state:
                    if new_val: region_grace_added = True
                    else: region_grace_removed = True
                    grace_item.setCheckState(new_state)
            if isinstance(region_item, RegionItem):
                region_item.update_count()
            # Only flash regions on non-startup major updates if needed
            if not is_startup and not is_expanded:
                self._handle_region_flash(region_item, region_grace_added, region_grace_removed)

    def update_search_box(self, text):
        if len(text) > 5:
            self.tree.expandAll()
        self.proxy_model.set_search_text(text)

    def on_context_menu(self, point):
        proxy_index = self.tree.indexAt(point)
        if not proxy_index.isValid():
            return
        
        source_index = self.proxy_model.mapToSource(proxy_index)
        item = self.base_model.itemFromIndex(source_index)

        menu = QMenu(self)
        if isinstance(item, GraceItem): # Boss Item
            action_copy = QAction("Copy Name", self)
            action_copy.triggered.connect(lambda: QApplication.clipboard().setText(item.text()))
            menu.addAction(action_copy)

            action_copy_id = QAction("Copy Event ID", self)
            action_copy_id.triggered.connect(lambda: QApplication.clipboard().setText(str(item.event_id)))
            menu.addAction(action_copy_id)

        elif isinstance(item, RegionItem):
            region_name = item.region_name
            is_expanded = self.tree.isExpanded(proxy_index)
            if is_expanded:
                action = QAction(f"Collapse {region_name}", self)
                action.triggered.connect(lambda: self.tree.collapse(proxy_index))
            else:
                action = QAction(f"Expand {region_name}", self)
                action.triggered.connect(lambda: self.tree.expand(proxy_index))
            menu.addAction(action)
        
        menu.exec(self.tree.viewport().mapToGlobal(point))

    def sync_ui_data(self, state: AppState):
        """This only runs when visible or upon opening."""
        # This is your existing update_with logic
        if state.current_character:
            self.update_with(state.current_character, state)



class BossFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, has_dlc):
        super().__init__()
        self.show_dlc = has_dlc
        self.show_checked_only = None
        self.search_text = ""

    def filterAcceptsRow(self, source_row, source_parent):
        model = cast(QStandardItemModel, self.sourceModel())
        index = model.index(source_row, 0, source_parent)
        item = model.itemFromIndex(index)

        if isinstance(item, RegionItem):
            for i in range(item.rowCount()):
                if self.filterAcceptsRow(i, index):
                    return True
            return False
        if not isinstance(item, GraceItem):
            return True #TODO: Maybe?
        
        if self.show_dlc is not None:
            if self.show_dlc and not item.dlc:
                return False
            elif not self.show_dlc and item.dlc:
                return False


        if self.show_checked_only is not None:
            if self.show_checked_only and item.checkState() != Qt.CheckState.Checked:
                return False
            elif not self.show_checked_only and item.checkState() == Qt.CheckState.Checked:
                return False

        if self.search_text:
            parent_item = item.parent()
            text = self.search_text.lower()
            if parent_item and text in parent_item.text().lower():
                return True
            if text not in item.text().lower():
                return False

        return True

    def set_show_checked_only(self, index: int):
        match index:
            case 0:
                new = None #Show all
            case 1:
                new = 1 #Checked
            case 2:
                new = 0 #Unchecked
            case _:
                raise ValueError(f"Undefined filter index for 'show_checked_only': {index}")
        if self.show_checked_only != new:
            self.show_checked_only = new
            self.invalidateFilter()

    def set_search_text(self, text: str):
        self.search_text = text
        self.invalidateFilter()

    def set_show_dlc(self, index: int):
        match index:
            case 0:
                new = None #Show all
            case 1:
                new = 0 #Don't show
            case 2:
                new = 1 #Only show
            case _:
                raise ValueError(f"Undefined filter index for 'set_show_dlc': {index}")
        if self.show_dlc != new:
            self.show_dlc = new
            self.invalidateFilter()