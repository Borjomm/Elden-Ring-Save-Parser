@echo off
cd /d "%~dp0"
if not exist ".venv" (
    echo Virtual environment not found. Running setup...
    python install.py
)
echo Starting Compilation...
".venv\Scripts\python.exe" -m app.wiki_stuff.update_wiki_db test_wiki.db "Elden Ring Great Archive" "Elden Ring Great Archive\public" --force_drop_table