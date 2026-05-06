import os
import sys
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable
from pathlib import Path
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QWidget, QLineEdit, QPushButton, QFileDialog, QLabel, QDialogButtonBox, QMessageBox, QMainWindow, QApplication

from app.data.containers import WikiSettingsContainer



class QFileDialogMode(Enum):
    FILE_MODE = auto()
    DIR_MODE = auto()

@dataclass(frozen=True)
class Condition:
    check: Callable[[Path], bool]
    invalid_text: str

    def test(self, path: Path):
        return self.check(path)

class PathRow(QWidget):
    def __init__(self, path: Path | None, checks: list[Condition] | None = None, mode: QFileDialogMode = QFileDialogMode.DIR_MODE, file_filter: str = "All Files (*.*)", callback: Callable[[bool], None] | None = None):
        super().__init__()
        self.checks = checks or []
        self.mode = mode
        self._path = path
        self.file_filter = file_filter
        self.callback = callback
        self.line_edit = QLineEdit(path.as_posix() if path else "", readOnly=True)
        self.button = QPushButton("Choose path...")
        self.button.clicked.connect(self.choose_folder)
        self.label = QLabel("")

        layout = QVBoxLayout(self)
        line_layout = QHBoxLayout()
        line_layout.addWidget(self.line_edit)
        line_layout.addWidget(self.button)
        layout.addLayout(line_layout)
        layout.addWidget(self.label)

        self.test_valid()

    def test_valid(self) -> bool:
        if self.path is None:
            return False
        for check in self.checks:
            if not check.test(self.path):
                self.label.setText(check.invalid_text)
                self.label.setStyleSheet("color: #ff6666; font-weight: bold;")
                return False
        self.label.setText("Accepted!")
        self.label.setStyleSheet("color: #66cc66; font-style: italic;")
        return True
    
    @property
    def path(self):
        return self._path
    
    @path.setter
    def path(self, new_path: Path | str):
        if isinstance(new_path, str):
            new_path = Path(new_path)
        self._path = new_path
        self.line_edit.setText(new_path.as_posix())
        result = self.test_valid()
        if self.callback is not None:
            self.callback(result)

    def choose_folder(self):
        path = self.path.as_posix() if self.path else os.getcwd()
        match self.mode:
            case QFileDialogMode.DIR_MODE:
                file_path = QFileDialog.getExistingDirectory(
                    self,
                    "Select a folder",
                    path
                )
            case QFileDialogMode.FILE_MODE:
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Select a file",
                    path,
                    filter=self.file_filter
                )
        if file_path:
            self.path = Path(file_path)

    def set_enabled(self, val: bool):
        self.line_edit.setEnabled(val)
        self.button.setEnabled(val)
        



class WikiSettingsDialog(QDialog):
    def __init__(self, parent=None, root_path = None, parse_path = None, db_path = None):
        super().__init__(parent)
        self.setWindowTitle("Wiki Settings")
        self.resize(600, 150)
        self.root_row = PathRow(root_path, [Condition(lambda p: p.is_dir(), "Path is not a valid directory!")], callback = self.enable_parse_dir)
        self.parse_row = PathRow(parse_path, [Condition(lambda p: p.is_dir(), "Path is not a valid directory!"), Condition(self.is_relative, "Path is not relative to the Root Path!")])
        self.db_row = PathRow(db_path or Path("app/gamedata.db"), [Condition(lambda p: p.suffix.lower() == ".db", "Path is not a valid database file!")], mode = QFileDialogMode.FILE_MODE, file_filter = "Database files (*.db)")
        self.items = [self.root_row, self.parse_row, self.db_row]

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.try_accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.addRow("Root Path", self.root_row)
        form_layout.addRow("Parse Path", self.parse_row)
        form_layout.addRow("Database Path", self.db_row)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

        self.enable_parse_dir(self.root_row.test_valid())
        

    def is_relative(self, parse_path: Path) -> bool:
        if self.root_row.path is None:
            return False
        return parse_path.resolve().is_relative_to(self.root_row.path.resolve())

    def enable_parse_dir(self, val):
        self.parse_row.set_enabled(val)
        if not val:
            return
        if self.parse_row.path is None and self.root_row.path is not None:
            self.parse_row.path = self.root_row.path
        else:
            self.parse_row.test_valid()

    def try_accept(self):
        if not all(item.test_valid() for item in self.items):
            QMessageBox.critical(self, "Error", "Some of the settings are invalid!")
        else:
            self.accept()
            

    def get_settings(self): # Only after accept!
        rp = self.root_row.path
        pp = self.parse_row.path
        dp = self.db_row.path
        if rp is None or pp is None or dp is None:
            raise ValueError("Settings container called without validation!")
        rel_str = pp.relative_to(rp).as_posix()
        strip_str = "" if rel_str == "." else f"{rel_str}/"
        return WikiSettingsContainer(
            rp.as_posix(),
            strip_str,
            dp.as_posix()
        )

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
        dialog = WikiSettingsDialog(self)
        
        # Use .exec() to make the window "Modal" (blocks the main window until closed)
        if dialog.exec():
            # If the user clicked "OK", this block runs
            settings = dialog.get_settings()
            print(settings.db_path)
            
            # Do something with the settings
            self.info_label.setText(
                "Approved!"
            )
        else:
            # If the user clicked "Cancel" or the 'X' button
            self.info_label.setText("Settings cancelled.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())





