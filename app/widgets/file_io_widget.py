import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QComboBox, QFileDialog

from core.app_state import AppStore
from core.save_controller import SaveController

class FileIOWidget(QWidget):
    def __init__(self, parent: QWidget, controller: SaveController, store: AppStore):
        super().__init__(parent)
        self.controller = controller
        
        # 1. Setup UI Elements
        self.line = QLineEdit(readOnly=True)
        self.button = QPushButton("Choose Save...")
        self.characters = QComboBox()

        layout = QHBoxLayout()
        layout.addWidget(self.line)
        layout.addWidget(self.button)
        layout.addWidget(self.characters)
        self.setLayout(layout)

        # 2. Wire up UI Intents (User actions)
        self.button.clicked.connect(self.on_browse_clicked)
        self.characters.currentIndexChanged.connect(self.on_combo_changed)

        # 3. Listen to the Application State
        store.state_changed.connect(self.update_from_state)

    def on_browse_clicked(self):
        """Pure UI logic: Just getting the string path from the OS."""
        # Using the controller to get a smart starting directory
        start_dir = self.controller.get_last_known_dir() or os.getcwd()
        
        file_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Select a savefile",
            dir=start_dir,
            filter="Elden Ring Savefiles (*.sl2);;Seamless Coop Savefiles (*.co2)"
        )
        
        if file_path:
            # Tell the brain what the user wants to do. We don't load it here!
            self.controller.open_new_file(file_path)

    def on_combo_changed(self, combo_index: int):
        """User picked a different character slot."""
        if combo_index < 0:
            return
            
        # Qt Trick: currentData() retrieves the hidden "real" slot index
        real_slot_index = self.characters.currentData()
        if real_slot_index is not None:
            self.controller.select_character_slot(real_slot_index)

    def update_from_state(self, state):
        """React to the AppState changing. No business logic allowed here!"""
        
        # Update text box
        if state.current_path and state.current_path != self.line.text():
            self.line.setText(state.current_path)

        # Update Dropdown if the file/headers changed
        # We block signals so clearing/adding items doesn't trigger on_combo_changed
        self.characters.blockSignals(True)
        self.characters.clear()

        if state.available_characters:
            for real_index, char_data in enumerate(state.available_characters):
                if char_data.name:  # Only add non-empty slots
                    display_text = f"{char_data.name} - SL{char_data.level}"
                    # We store the `real_index` inside the item data!
                    self.characters.addItem(display_text, userData=real_index)

            # Sync the dropdown visual selection with the AppState
            if state.current_slot is not None:
                # Find which dropdown item contains our real slot index
                for i in range(self.characters.count()):
                    if self.characters.itemData(i) == state.current_slot:
                        self.characters.setCurrentIndex(i)
                        break

        self.characters.blockSignals(False)