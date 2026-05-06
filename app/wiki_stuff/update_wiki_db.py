
import sqlite3
import frontmatter
import re
import json
import sys
from urllib.parse import quote
from pathlib import Path

from app.wiki_stuff.wiki_engine import EldenWikiEngine
from app.infrastructure.settings_repository import SettingsRepository
from app.data.containers import WikiSettingsContainer
from app.data.consts import MAIN_DB_PATH

from PySide6.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QDialogButtonBox, QLineEdit, QPushButton, QMessageBox, QApplication, QCheckBox

class WikiParser:
    wikilink_pattern = re.compile(r'\[\[([^|\]]+)(?:\|([^\]]+))?\]\]')
    def __init__(self, settings: WikiSettingsContainer, drop_table: bool = False):
        self.conn = sqlite3.connect(settings.db_path)
        self.folder_path = Path(settings.root_path, settings.parse_path)
        self.files = self.folder_path.rglob("*.md")
        self.strip_str = settings.parse_path
        self.drop_table = drop_table

    def _link_replacer(self, match):
        raw_target = match.group(1).strip()
        alias = match.group(2).strip() if match.group(2) else None
            
        # 1. Strip 'public/' if it exists
        if raw_target.startswith(self.strip_str):
            target = raw_target.removeprefix(self.strip_str)
        else:
            target = raw_target

        # 2. If no alias was provided, default to the stripped target
        # So [[public/Radahn]] becomes "Radahn" instead of "public/Radahn"
        if not alias:
            alias = target
        safe_target = quote(target)
        # We use a custom 'wiki://' protocol so PySide knows it's an internal link
        return f"[{alias}](wiki:{safe_target})"

    def make_table(self):
        if self.drop_table:
            self.conn.execute("DROP TABLE IF EXISTS wiki_entries")
        self.conn.execute("""
CREATE TABLE IF NOT EXISTS wiki_entries (
filepath TEXT PRIMARY KEY,
name TEXT NOT NULL,
markdown TEXT,
hidden_markdown TEXT,
conditions TEXT,
unlock_ids TEXT)
""")
        self.conn.commit()

    def parse_md(self):
        self.make_table()
        query = [self._parse_file(file) for file in self.files]
        self.conn.executemany("""
INSERT INTO wiki_entries (filepath, name, markdown, hidden_markdown, conditions, unlock_ids) VALUES (?, ?, ?, ?, ?, ?)
""", query)
        self.conn.commit()
        return len(query)

    def _parse_file(self, path: Path):
        print(f"Parsing {path}")
        save_path = path.relative_to(self.folder_path)
        post = frontmatter.load(str(path))
        current_markdown = self.wikilink_pattern.sub(self._link_replacer, post.content)
        hidden_markdown = post.metadata.get("hidden")
        unlock_ids = post.metadata.get("unlock_ids")
        if not isinstance(unlock_ids, list):
            unlock_ids = []

        event_dict = EldenWikiEngine.extract_all_ids(current_markdown, unlock_ids)
        return (save_path.as_posix(), path.stem, current_markdown, hidden_markdown, json.dumps(event_dict), ",".join(unlock_ids))
    
class UpdateUI(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Database Compiler")
        self.resize(600, 150)
        self.settings = SettingsRepository()
        container = self.settings.get_or_prompt_wiki_settings()
        if not container:
            sys.exit(1)
        self.container = container
        change_settings_button = QPushButton("Change settings...")
        change_settings_button.clicked.connect(self.change_container)
        self.root_line = QLineEdit(container.root_path, readOnly=True)
        self.parse_line = QLineEdit(container.parse_path, readOnly=True)
        self.db_line = QLineEdit(container.db_path, readOnly=True)
        self.drop_table_checkbox = QCheckBox()
        self.drop_table_checkbox.setChecked(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.parse_into_db)
        buttons.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.addRow("Obsidian vault folder", self.root_line)
        form_layout.addRow("Parsing folder", self.parse_line)
        form_layout.addRow("Output path", self.db_line)
        form_layout.addRow("Replace old data", self.drop_table_checkbox)

        main_layout.addWidget(change_settings_button)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(buttons)

    def parse_into_db(self):
        drop_table = self.drop_table_checkbox.isChecked()
        result = QMessageBox.StandardButton.Ok
        if self.container.db_path == MAIN_DB_PATH:
            msg = "You are about to overwrite the main database table!" if drop_table else "You are about to commit to the main database table!"
            result = QMessageBox.question(
                self,
                "Confirm Action",
                msg + " Make sure to backup your database before clicking 'Ok'.",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            )
        if result == QMessageBox.StandardButton.Ok:
            try:
                parser = WikiParser(self.container, drop_table)
                num_files = parser.parse_md()
                QMessageBox.information(self, "Success", f"The database has been updated successfully, {num_files} {'written' if drop_table else 'added'}.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error while parsing the database:\n{e}")
                self.reject()


    def change_container(self):
        container = self.settings.prompt_wiki_settings()
        if not container:
            return
        self.container = container
        self.root_line.setText(container.root_path)
        self.parse_line.setText(container.parse_path)
        self.db_line.setText(container.db_path)


def main():
    app = QApplication()
    app.setStyle("Fusion")
    settings = SettingsRepository()
    container = settings.get_or_prompt_wiki_settings()
    if not container:
        return
    parser = UpdateUI()
    parser.exec()
            

if __name__ == "__main__":
    main()