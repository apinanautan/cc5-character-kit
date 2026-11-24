@echo off
setlocal
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
py -3 "%~dp0tools\ai_cc5.py" %*
