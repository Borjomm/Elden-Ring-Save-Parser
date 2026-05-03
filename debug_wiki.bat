@echo off
cd /d "%~dp0"
if not exist ".venv" (
    echo Virtual environment not found. Running setup...
    python install.py
)
echo Starting Elden Ring Wiki Debug View...
".venv\Scripts\python.exe" -m app.wiki_stuff.main_wiki
pause