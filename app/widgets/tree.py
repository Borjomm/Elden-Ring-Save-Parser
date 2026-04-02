
from PySide6.QtWidgets import QTreeView, QVBoxLayout, QWidget, QLineEdit, QCheckBox, QHBoxLayout, QPushButton, QLabel, QMenu, QApplication
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction, QDesktopServices
from PySide6.QtCore import Qt, QSortFilterProxyModel, QUrl
from typing import cast
from sqlite3 import Connection

from app.parser.wrapper import CharacterData
from app.data.consts import DLC, OFFSET, REMEMBRANCE, LINK, QT_GREEN, QT_RED, QT_YELLOW, REGION_NAME
from app.core.app_state import AppStore, AppState
from app.util.utils import make_combo_widget
from app.util.animation import flash_item

class BossWindow(QWidget):
    def __init__(self, connection: Connection, store: AppStore):
        super().__init__()
        self.connection = connection
        self.has_dlc = True
        self.setWindowTitle("Boss Tracker")

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

        self.remembrance = QCheckBox

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

        store.state_changed.connect(self.on_state_updated)

    def populate_model(self):
        root_item = self.base_model.invisibleRootItem()
        region_items = {}

        query = "SELECT * FROM bosses ORDER BY is_dlc, region, name"
        cursor = self.connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        self.base_model.layoutAboutToBeChanged.emit()
        for boss_id, boss_name, region, remembrance, dlc, save_bit_offset, link in rows:
            if region not in region_items:
                region_item = QStandardItem()
                region_item.setEditable(False)
                region_item.setData(region, REGION_NAME)
                root_item.appendRow(region_item)
                region_items[region] = region_item

            parent_item = region_items[region]
            boss_item = QStandardItem(boss_name)
            boss_item.setEditable(False)
            boss_item.setCheckable(False)
            boss_item.setCheckState(Qt.CheckState.Unchecked)

            boss_item.setData(remembrance, REMEMBRANCE)
            boss_item.setData(dlc, DLC)
            boss_item.setData(save_bit_offset, OFFSET)
            boss_item.setData(link, LINK)

            parent_item.appendRow(boss_item)

        self.base_model.layoutChanged.emit()

    def update_all_region_counts(self):
        for i in range(self.base_model.rowCount()):
            region_item = self.base_model.item(i)
            self.update_region_count(region_item)

    def update_region_count(self, region_item: QStandardItem):
        total = region_item.rowCount()
        checked = sum(1 for i in range(total) if region_item.child(i).checkState() == Qt.CheckState.Checked)
        region_name = region_item.data(REGION_NAME)
        region_item.setText(f"{region_name} ({checked}/{total})")

    def update_with(self, data: CharacterData, state: AppState):
        self.has_dlc = data.has_dlc()
        root_item = self.base_model.invisibleRootItem()
        self.base_model.layoutAboutToBeChanged.emit()
        tree_changed = False
        is_startup = state.time_since_start() < 1.0

        for i in range(root_item.rowCount()):
            region_item = root_item.child(i)
            region_boss_added = False
            region_boss_removed = False
            region_index = region_item.index()
            region_proxy_index = self.proxy_model.mapFromSource(region_index)
            is_region_visible = region_proxy_index.isValid()
            is_region_expanded = True
            if is_region_visible:
                is_region_expanded = self.tree.isExpanded(region_proxy_index)
            
            for j in range(region_item.rowCount()):
                boss_item = region_item.child(j)
                offset = boss_item.data(OFFSET)
                new_state = Qt.CheckState.Checked if data.get_flag(offset) else Qt.CheckState.Unchecked
                check_state = boss_item.checkState()
                if new_state != check_state:
                    tree_changed = True
                    print(f"Updated boss: {boss_item.text()}")
                    if new_state == Qt.CheckState.Checked:
                        region_boss_added = True
                        if state.time_since_watching() > 1.0:
                            self.bottom_text_bar.setText(f"Boss slain: {boss_item.text()}")
                            if is_region_visible and not is_region_expanded:
                                self.tree.expand(region_proxy_index)
                                is_region_expanded = True
                    else:
                        region_boss_removed = True
                    boss_item.setCheckState(new_state)

                    # Animation
                    is_boss_visible = self.proxy_model.mapFromSource(boss_item.index()).isValid()
                    if is_boss_visible and is_region_visible and is_region_expanded and not is_startup:
                        flash_item(self.base_model, boss_item.index(), QT_GREEN if new_state == Qt.CheckState.Checked else QT_RED)

            self.update_region_count(region_item)

            # Animation
            if not is_region_expanded and not is_startup:
                if region_boss_added and region_boss_removed:
                    flash_item(self.base_model, region_index, QT_YELLOW)
                elif region_boss_added:
                    flash_item(self.base_model, region_index, QT_GREEN)
                elif region_boss_removed:
                    flash_item(self.base_model, region_index, QT_RED)
        
        if not tree_changed and state.time_since_last_save() > 5.0:
            self.bottom_text_bar.setText("")
        self.base_model.layoutChanged.emit()

    def update_search_box(self, text):
        if len(text) > 5:
            self.tree.expandAll()
        self.proxy_model.set_search_text(text)

    def on_state_updated(self, state: AppState):
        if state.is_loading:
            return
        
        if state.current_character:
            self.update_with(state.current_character, state)

    def on_context_menu(self, point):
        proxy_index = self.tree.indexAt(point)
        if not proxy_index.isValid():
            return
        
        source_index = self.proxy_model.mapToSource(proxy_index)
        item = self.base_model.itemFromIndex(source_index)

        menu = QMenu(self)
        if not item.hasChildren(): # Boss Item
            link = item.data(LINK)
            if link:
                action_wiki = QAction(f"Open Wiki: {item.text()}", self)
                action_wiki.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(link)))
                menu.addAction(action_wiki)

            action_copy = QAction("Copy Name", self)
            action_copy.triggered.connect(lambda: QApplication.clipboard().setText(item.text()))
            menu.addAction(action_copy)

        else: # Region Item
            region_name = item.data(REGION_NAME)
            is_expanded = self.tree.isExpanded(proxy_index)
            if is_expanded:
                action = QAction(f"Collapse {region_name}", self)
                action.triggered.connect(lambda: self.tree.collapse(proxy_index))
            else:
                action = QAction(f"Expand {region_name}", self)
                action.triggered.connect(lambda: self.tree.expand(proxy_index))
            menu.addAction(action)
        
        menu.exec(self.tree.viewport().mapToGlobal(point))



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

        if item.hasChildren():
            for i in range(item.rowCount()):
                if self.filterAcceptsRow(i, index):
                    return True
            return False

        if self.show_dlc is not None:
            if self.show_dlc and not item.data(DLC):
                return False
            elif not self.show_dlc and item.data(DLC):
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