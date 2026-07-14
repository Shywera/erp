@echo off
cd /d "%~dp0"
echo Pokrecem ERP server (lokalno)...
echo Otvori: http://localhost:8000
echo.
.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
