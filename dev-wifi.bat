@echo off
cd /d "%~dp0"
echo Pokrecem ERP server (WiFi mreza)...
echo Lokalno:  http://localhost:8000
echo Mreza:    http://192.168.1.8:8000
echo.
echo NAPOMENA: Ako drugi komp ne moze pristupiti, pokrenite jednom kao Admin:
echo   netsh advfirewall firewall add rule name="ERP dev 8000" dir=in action=allow protocol=TCP localport=8000
echo.
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
