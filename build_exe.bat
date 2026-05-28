@echo off
chcp 65001 >nul
title MorphVPN — Сборка EXE

echo.
echo  Устанавливаю PyInstaller...
pip install pyinstaller -q

echo  Собираю EXE...
pyinstaller --onefile --windowed --name "MorphVPN_Launcher" --icon=NONE launcher.py

echo.
echo  Готово! EXE находится в папке dist\
echo  Файл: dist\MorphVPN_Launcher.exe
echo.
pause
