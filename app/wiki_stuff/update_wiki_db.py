import argparse
import sqlite3
import frontmatter
import re
import json
from urllib.parse import quote
from pathlib import Path

from app.wiki_stuff.wiki_engine import EldenWikiEngine

class WikiParser:
    wikilink_pattern = re.compile(r'\[\[([^|\]]+)(?:\|([^\]]+))?\]\]')
    def __init__(self, db_path: Path, f_path: Path, strip_str: str, drop_table: bool = False):
        self.conn = sqlite3.connect(db_path)
        self.folder_path = f_path
        self.files = f_path.rglob("*.md")
        self.strip_str = strip_str
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('db_path')
    parser.add_argument('root_path')
    parser.add_argument('folder_path')
    parser.add_argument('-f', "--force_drop_table", action="store_true")
    parser.add_argument('-v', "--verbose", action="store_true")
    args = parser.parse_args()
    db_path = Path(args.db_path)
    root_path = Path(args.root_path)
    folder_path = Path(args.folder_path)

    if not db_path.suffix == ".db":
        print("Error: Database path is not a database file.")
        return
    if not root_path.is_dir():
        print(f"Error: Root path '{root_path}' does not exist or is not a directory.")
        return
    elif not folder_path.is_dir():
        print(f"Error: Folder path '{folder_path}' does not exist or is not a directory.")
        return
    if db_path.stem == "gamedata":
        prompt = "You are about to permanently replace the main wiki_entries table!" if args.force_drop_table else "You are about to add entries to the main wiki_entries table!"
        response = input(prompt + " Make a backup of gamedata.db and type 'YES' afterwards: ")
        if response != "YES":
            print("Exiting...")
            return
    # Resolve paths to absolute paths to prevent comparison errors
    res_root = root_path.resolve()
    res_folder = folder_path.resolve()

        # 2. Check if folder_path is within root_path (Requires Python 3.9+)
    if not res_folder.is_relative_to(res_root):
        print(f"Error: '{res_folder}' is completely outside of '{res_root}'.")
        return
            
            # 3. Output the difference
    wikilink_strip_str = res_folder.relative_to(res_root).as_posix() + "/"
    parser = WikiParser(db_path, folder_path, wikilink_strip_str, args.force_drop_table)
    parser.parse_md()
            

if __name__ == "__main__":
    main()