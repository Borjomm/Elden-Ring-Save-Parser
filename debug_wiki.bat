@echo off
call ensure_env.bat || exit /b 1

echo Starting Elden Ring Wiki Debug View...
".venv\Scripts\python.exe" -m app.wiki_stuff.main_wiki
pause