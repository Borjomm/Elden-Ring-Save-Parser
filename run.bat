@echo off
setlocal enabledelayedexpansion

if not exist ".venv" (
    echo Virtual environment not found. Running setup...
    python install.py
    goto :launch
)

if exist "requirements.txt" (
    :: 1. Calculate SHA256 of requirements.txt
    set "CURR_HASH="
    for /f "skip=1 tokens=* delims=" %%# in ('certutil -hashfile requirements.txt SHA256') do (
        if not defined CURR_HASH set "CURR_HASH=%%#"
    )
    set "CURR_HASH=!CURR_HASH: =!"

    :: 2. Read previously saved hash and strip whitespace
    set "SAVED_HASH="
    if exist ".venv\requirements.sha" (
        set /p SAVED_HASH=<.venv\requirements.sha
        set "SAVED_HASH=!SAVED_HASH: =!"
    )

    :: 3. Compare hashes
    if not "!CURR_HASH!"=="!SAVED_HASH!" (
        echo requirements.txt has changed. Updating dependencies...
        ".venv\Scripts\python.exe" -m pip install -r requirements.txt
        >".venv\requirements.sha" echo !CURR_HASH!
    )
)

:launch
echo Starting Elden Ring Save Inspector...
".venv\Scripts\python.exe" main.py
pause