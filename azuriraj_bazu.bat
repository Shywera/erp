@echo off
cd /d "%~dp0"

.venv\Scripts\python -m alembic upgrade head

echo.
echo Baza azurirana.
pause
