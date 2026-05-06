import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QCheckBox, QDialogButtonBox, QPushButton, QLabel
)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(300, 150)

        # 1. Create Layouts
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout() # Perfect for "Label: Input" settings

        # 2. Create Settings Widgets
        self.username_input = QLineEdit()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System Default", "Light", "Dark"])
        
        self.notifications_check = QCheckBox("Enable desktop notifications")
        self.notifications_check.setChecked(True)

        # 3. Add widgets to the form layout
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Theme:", self.theme_combo)
        form_layout.addRow("", self.notifications_check) # Empty label for checkbox

        # 4. Create OK and Cancel buttons
        # QDialogButtonBox automatically formats buttons to match your OS style (Windows/Mac/Linux)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        # Connect the buttons to the Dialog's built-in accept/reject slots
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # 5. Add everything to the main layout
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

    # Helper method to extract the data easily
    def get_settings(self):
        return {
            "username": self.username_input.text(),
            "theme": self.theme_combo.currentText(),
            "notifications": self.notifications_check.isChecked()
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Application")
        self.resize(400, 300)

        # Main window layout
        layout = QVBoxLayout()
        
        self.info_label = QLabel("Click the button to open settings.")
        layout.addWidget(self.info_label)

        settings_btn = QPushButton("Open Settings")
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)

        # Set central widget
        central_widget = QDialog()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_settings(self):
        # Create the dialog, passing 'self' so it acts as a child of the main window
        dialog = SettingsDialog(self)
        
        # Use .exec() to make the window "Modal" (blocks the main window until closed)
        if dialog.exec():
            # If the user clicked "OK", this block runs
            settings = dialog.get_settings()
            
            # Do something with the settings
            self.info_label.setText(
                f"Saved!\nUser: {settings['username']}\n"
                f"Theme: {settings['theme']}\n"
                f"Notifications: {settings['notifications']}"
            )
        else:
            # If the user clicked "Cancel" or the 'X' button
            self.info_label.setText("Settings cancelled.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())