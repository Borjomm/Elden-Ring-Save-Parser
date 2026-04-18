import sqlite3
from collections.abc import Iterable

def get_connection(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_temp_db(db_path: str) -> None:
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS screenshots (
                    screenshot_id INTEGER PRIMARY KEY,
                    image_link TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    val INTEGER,
                    description TEXT NOT NULL,
                    category TEXT,
                    tags TEXT,
                    screenshot_id INTEGER,
                    FOREIGN KEY (screenshot_id) REFERENCES screenshots(screenshot_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS regions (
                    region_id INTEGER PRIMARY KEY,
                    description TEXT NOT NULL
                )
            """)
    finally:
        conn.close()
    

def save_rows(
    db_path: str,
    rows_screenshots: Iterable[tuple[int, str]],
    rows_events: Iterable[tuple[int, int, str, str, str, int]],
    rows_regions: Iterable[tuple[int, str]],
) -> None:
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("PRAGMA foreign_keys = ON")

            conn.executemany("""
                INSERT OR IGNORE INTO screenshots (screenshot_id, image_link)
                VALUES (?, ?)
            """, rows_screenshots)

            conn.executemany("""
                INSERT OR IGNORE INTO events (event_id, val, description, category, tags, screenshot_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, rows_events)

            conn.executemany("""
                INSERT OR IGNORE INTO regions (region_id, description)
                VALUES (?, ?)
            """, rows_regions)

            conn.commit()
    finally:
        conn.close()