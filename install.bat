@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul || (echo Python not found - install Python 3.11+ from python.org and tick "Add to PATH" & pause & exit /b 1)
python tools\install.py
pause
