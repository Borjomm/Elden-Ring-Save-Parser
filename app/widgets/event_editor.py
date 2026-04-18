from app.data.containers import DisplayedDeltaChange
from datetime import datetime
from sqlite3 import Connection

from PySide6.QtWidgets import QWidget, QTreeView, QVBoxLayout, QSplitter, QLineEdit, QLabel, QHBoxLayout, QFormLayout, QPushButton, QSizePolicy
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QImage
from PySide6.QtCore import Qt

from app.core.save_controller import SaveController
from app.data.containers import EventFlag
from app.util.db import save_rows, init_temp_db
from app.data.consts import TEMP_DB_PATH

class AspectRatioLabel(QLabel):
    def __init__(self, text="No Image", parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(200, 150)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._pixmap = None

    def setPixmap(self, pixmap: QPixmap | QImage):
        self._pixmap = pixmap
        self.update_pixmap()

    def update_pixmap(self):
        if self._pixmap and not self._pixmap.isNull():
            # Scale the image to fit the current label size while keeping proportions
            scaled = self._pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled)

    def resizeEvent(self, event):
        """This fires whenever the splitter moves or the window resizes."""
        self.update_pixmap()
        super().resizeEvent(event)

class DetailEditor(QWidget):
    def __init__(self, parent: "EventEditor"):
        super().__init__()
        self.editor_parent = parent
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight) # Optional: labels right-aligned

        # Add rows directly
        self.id = QLineEdit(readOnly=True)
        self.description = QLineEdit()
        self.category = QLineEdit()
        self.tags = QLineEdit()
        self.submit_button = QPushButton("Submit")
        self.clear_button = QPushButton("Clear")
        self.submit_button.clicked.connect(self.submit)
        self.clear_button.clicked.connect(self.unload)

        form_layout.addRow("Event ID:", self.id)
        form_layout.addRow("Description:", self.description)
        form_layout.addRow("Category:", self.category)
        form_layout.addRow("Tags:", self.tags)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.clear_button)
        self.image_label = AspectRatioLabel("No Image Loaded")

        # Set the form layout into your main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.image_label)

    def toggle_edit(self, val: bool):
        self.id.setEnabled(val)
        self.description.setEnabled(val)
        self.category.setEnabled(val)
        self.tags.setEnabled(val)

    def load(self, event: EventFlag, screenshot_path: str):
        self.id.setText(str(event.event_id))
        self.description.setText(event.description)
        self.category.setText(event.category)
        self.tags.setText(event.tags)
        pixmap = QPixmap(screenshot_path)
        self.image_label.setPixmap(pixmap)
        self.toggle_edit(True)

    def unload(self):
        self.id.clear()
        self.description.clear()
        self.category.clear()
        self.tags.clear()
        self.image_label.clear()
        self.toggle_edit(False)

    def submit(self):
        if not self.id.text():
            return
        new_flag = EventFlag(int(self.id.text()), self.description.text(), self.category.text(), self.tags.text())
        self.editor_parent.submit_item(new_flag)
        self.unload()


class EventEditor(QWidget):

    def __init__(self, db_connection: Connection, controller: SaveController):
        super().__init__()
        self.conn = db_connection
        self.temp_db_path = TEMP_DB_PATH
        self.controller = controller
        self.id_to_items: dict[int, list[QStandardItem]] = {}
        self.screenshots: dict[int, str] = {}
        
        self.splitter = QSplitter(self)
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.tree_view.doubleClicked.connect(self.on_item_double_clicked)
        self.detail_view = DetailEditor(self)

        self.splitter.addWidget(self.tree_view)
        self.splitter.addWidget(self.detail_view)
        self.splitter.setSizes([7000, 3000])

        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)
        self.setLayout(layout)
        self.temp_db_init = False
        self.dirty = False


        self.controller.event_tracker.new_change_recorded.connect(self.add_change_to_view)

    def map_item(self, item: QStandardItem, event_id: int):
        if event_id not in self.id_to_items:
            self.id_to_items[event_id] = [item]
        else:
            self.id_to_items[event_id].append(item)

    def add_change_to_view(self, change: DisplayedDeltaChange):
        """Receiver: Triggered whenever a new delta group is captured."""
        
        # 1. Create the Top-Level (Parent) Row for the Screenshot/Timestamp
        self.screenshots[change.timestamp] = change.screenshot_path

        time_str = datetime.fromtimestamp(change.timestamp / 1000).strftime('%H:%M:%S')
        parent_item = QStandardItem(f"Capture @ {time_str} ({len(change)} flags)")
        parent_item.setData(change, Qt.ItemDataRole.UserRole) # Store the whole object for later
        parent_item.setEditable(False)
        
        # Add the parent row to the model
        self.model.appendRow(parent_item)
        
        # 2. Create child rows for every flag in this delta
        for flag in change.flags:
            child = QStandardItem(str(flag))
            child.setData(flag, Qt.ItemDataRole.UserRole)
            child.setEditable(False)
            
            parent_item.appendRow(child)
            self.map_item(child, flag.event_id)
        self.dirty = True

    def submit_item(self, event: EventFlag):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO event_dictionary (
                    event_id, 
                    description, 
                    category, 
                    tags
                ) VALUES (?, ?, ?, ?)
            """, (
                event.event_id, 
                event.description, 
                event.category, 
                event.tags
            ))
            self.conn.commit()
            
        except Exception as e:
            print(f"Database error: {e}")
            # You might want to show a message box here later
            return
        self.controller.event_tracker.flags[event.event_id] = event
        items = self.id_to_items.get(event.event_id)
        if not items:
            return
        for item in items:
            old_event = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(old_event, EventFlag):
                event = event.add_temp_info(old_event.screenshot_id, old_event.display_val)
            item.setData(event, Qt.ItemDataRole.UserRole)
            item.setText(str(event))
        

    def on_item_double_clicked(self, index):
        item = self.model.itemFromIndex(index)
        data = item.data(Qt.ItemDataRole.UserRole)

        # 1. Check if the clicked item is an EventFlag (child)
        if isinstance(data, EventFlag):
            # 2. Get the screenshot path from the parent (the Capture header)
            parent_index = index.parent()
            if parent_index.isValid():
                parent_item = self.model.itemFromIndex(parent_index)
                capture_data = parent_item.data(Qt.ItemDataRole.UserRole) # DisplayedDeltaChange
                
                # 3. Load into the DetailEditor
                self.detail_view.load(data, capture_data.screenshot_path)

        # 4. Optional: If clicking the parent itself, clear or show full screenshot?
        elif isinstance(data, DisplayedDeltaChange):
            self.detail_view.unload()

    def gather_session_data(self):
        """Iterates through the UI model to prepare data for the database."""
        rows_screenshots = []
        rows_events = []
        
        # 1. Iterate through Top-Level items (Captures/Screenshots)
        for i in range(self.model.rowCount()):
            parent_item = self.model.item(i)
            change_data = parent_item.data(Qt.ItemDataRole.UserRole) # DisplayedDeltaChange
            
            if not change_data:
                continue
                
            # Add to screenshot list (timestamp, path)
            rows_screenshots.append((change_data.timestamp, change_data.screenshot_path))
            
            # 2. Iterate through children of this Capture (EventFlags)
            for j in range(parent_item.rowCount()):
                child_item = parent_item.child(j)
                flag = child_item.data(Qt.ItemDataRole.UserRole) # EventFlag
                
                if flag:
                    # Prepare row for 'events' table
                    # (event_id, val, description, category, tags, screenshot_id)
                    rows_events.append((
                        flag.event_id,
                        flag.display_val,
                        flag.description,
                        flag.category,
                        flag.tags,
                        change_data.timestamp # Use timestamp as the ID link
                    ))
                    
        # 3. Get new regions from the tracker (they are static definitions)
        rows_regions = [(k, v) for k, v in self.controller.event_tracker.new_regions.items()]
        
        return rows_screenshots, rows_events, rows_regions

    def save_session_to_temp_db(self):
        # 1. Gather data from the UI
        screenshots, events, regions = self.gather_session_data()
        
        if not screenshots:
            print("Nothing to save.")
            return

        # 2. Initialize the DB if needed
        tracker = self.controller.event_tracker
        if not self.temp_db_init:
            init_temp_db(self.temp_db_path)
            self.temp_db_init = True
            
        # 3. Save using your infrastructure function
        # Note: Using INSERT OR REPLACE is important here so edits overwrite placeholders
        save_rows(self.temp_db_path, screenshots, events, regions)
        
        print(f"Session saved: {len(events)} flags logged.")