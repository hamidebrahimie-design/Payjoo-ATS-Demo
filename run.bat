@echo off
setlocal

title Payjoo ATS v1.5.5

cd /d %~dp0

set PYTHONPATH=%~dp0

:: Try default python, fallback to LobsterAI bundled Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python not found in PATH, using LobsterAI bundled Python...
    set PYTHON_EXE=C:\Users\PC\AppData\Roaming\LobsterAI\runtimes\python-win\python.exe
) else (
    set PYTHON_EXE=python
)

start "" http://127.0.0.1:8000/

%PYTHON_EXE% runner.py

echo.
echo Server stopped.
pause
