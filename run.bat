@echo off
if not exist ".venv" (
    echo Virtual environment not found. Running setup...
    python install.py
)
echo Starting Elden Ring Save Inspector...
".venv\Scripts\python.exe" main.py
pause