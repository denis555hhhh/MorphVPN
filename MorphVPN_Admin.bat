@echo off
chcp 65001 >nul
title MorphVPN Launcher
set TOKEN=8753394596:AAEA67fhil5B_R9iP-j5M5ZnIoOjhkykxDA
set DATABASE_URL=
cd /d "%~dp0"
python launcher.py
pause
