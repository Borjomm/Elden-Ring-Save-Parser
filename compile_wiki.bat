@echo off
cd /d "%~dp0"
if not exist ".venv" (
    echo Virtual environment not found. Running setup...
    python install.py
)
echo Starting Compilation...
:: Replace database argument with "app/gamedata.db" to update the main app
".venv\Scripts\python.exe" -m app.wiki_stuff.update_wiki_db "app/gamedata.db" "Elden Ring Great Archive" "Elden Ring Great Archive\public" --force_drop_table