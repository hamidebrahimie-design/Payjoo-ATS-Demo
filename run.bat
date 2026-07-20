@echo off
title Payjoo ATS v1.5.5

cd /d %~dp0

set PYTHONPATH=%~dp0

start "" http://127.0.0.1:8000/

python runner.py

pause
