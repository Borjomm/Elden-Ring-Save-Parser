@echo off
call ensure_env.bat || exit /b 1

echo Starting Compilation...
:: Replace database argument with "app/gamedata.db" to update the main app
".venv\Scripts\python.exe" -m app.wiki_stuff.update_wiki_db