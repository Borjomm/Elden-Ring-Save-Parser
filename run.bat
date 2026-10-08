@echo off
call ensure_env.bat || exit /b 1

echo Starting Elden Ring Save Inspector...
".venv\Scripts\python.exe" main.py
pause