@echo off
cd /d "%~dp0"

if not exist .venv (
    echo Stvaram virtualno okruzenje...
    python -m venv .venv
)

echo Instaliram potrebne pakete...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt

echo Postavljam bazu podataka...
.venv\Scripts\python -m alembic upgrade head

echo.
echo Gotovo. Sada mozes pokrenuti pokreni.bat
pause
