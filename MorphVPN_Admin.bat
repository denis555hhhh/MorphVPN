@echo off
chcp 65001 >nul
title MorphVPN — Панель администратора

:: ─── Переменные окружения ───────────────────────────────────────────────────
set TOKEN=8753394596:AAEA67fhil5B_R9iP-j5M5ZnIoOjhkykxDA

:: DATABASE_URL — вставь сюда строку подключения с Railway
:: Формат: postgresql://user:password@host:port/dbname
:: Найти на Railway: проект → PostgreSQL → Variables → DATABASE_URL
set DATABASE_URL=

:: ─── Путь к папке проекта ───────────────────────────────────────────────────
set PROJECT_DIR=%~dp0

:: ─── Проверка Python ────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ОШИБКА] Python не найден!
    echo  Скачай Python с https://python.org
    echo.
    pause
    exit /b 1
)

:: ─── Запуск панели ──────────────────────────────────────────────────────────
cd /d "%PROJECT_DIR%"
python admin_panel.py

pause
