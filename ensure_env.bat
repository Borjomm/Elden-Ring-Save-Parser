@echo off
setlocal enabledelayedexpansion

:: Optional arguments with defaults:
:: %1 = requirements file (default: requirements.txt)
:: %2 = venv folder (default: .venv)
set "REQ_FILE=%~1"
if "%REQ_FILE%"=="" set "REQ_FILE=requirements.txt"

set "VENV_DIR=%~2"
if "%VENV_DIR%"=="" set "VENV_DIR=.venv"

:: 1. Ensure virtual environment exists
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Virtual environment not found in "%VENV_DIR%". Running setup...
    if exist "install.py" (
        python install.py
    ) else (
        echo Creating virtual environment...
        python -m venv "%VENV_DIR%"
    )
)

:: 2. Check requirements hash
if exist "%REQ_FILE%" (
    :: Calculate SHA256 of the requirements file
    set "CURR_HASH="
    for /f "skip=1 tokens=* delims=" %%# in ('certutil -hashfile "%REQ_FILE%" SHA256') do (
        if not defined CURR_HASH set "CURR_HASH=%%#"
    )
    set "CURR_HASH=!CURR_HASH: =!"

    :: Name the hash file after the requirements file
    set "HASH_FILE=%VENV_DIR%\%~nx1.sha"
    if "%~1"=="" set "HASH_FILE=%VENV_DIR%\requirements.sha"

    :: Read previously saved hash and strip whitespace
    set "SAVED_HASH="
    if exist "!HASH_FILE!" (
        set /p SAVED_HASH=<"!HASH_FILE!"
        set "SAVED_HASH=!SAVED_HASH: =!"
    )

    :: Compare hashes and update if different
    if not "!CURR_HASH!"=="!SAVED_HASH!" (
        echo %REQ_FILE% has changed. Updating dependencies...
        "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%REQ_FILE%"
        
        :: Only record the new hash if pip succeeded
        if !errorlevel! equ 0 (
            >"!HASH_FILE!" echo !CURR_HASH!
        ) else (
            echo Failed to install dependencies.
            exit /b !errorlevel!
        )
    )
)

endlocal