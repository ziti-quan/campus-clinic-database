@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
chcp 65001 >nul

echo ============================================================
echo   Campus Clinic Database Project - Frontend Screenshots
echo ============================================================
echo.
echo This window will:
echo   1. start the three Flask apps (if not running)
echo   2. drive Edge headless to log in and switch every view
echo   3. save PNG files into the project screenshot folder
echo.

where python >nul 2>nul
if "%errorlevel%"=="0" goto use_python

where py >nul 2>nul
if "%errorlevel%"=="0" goto use_py_launcher

echo [ERROR] Python not found in PATH.
echo         Install Python or run auto_shoot.py manually.
goto end

:use_python
python auto_shoot.py
set RC=%errorlevel%
goto report

:use_py_launcher
py auto_shoot.py
set RC=%errorlevel%
goto report

:report
echo.
if not "%RC%"=="0" echo [FAILED] exit code %RC%
if not "%RC%"=="0" echo   If a module is missing, run:
if not "%RC%"=="0" echo       pip install requests websocket-client
if not "%RC%"=="0" echo   If Edge is missing, edit EDGE_CANDIDATES in auto_shoot.py
if "%RC%"=="0" echo [DONE] Screenshots saved. See the exact path printed above.

:end
echo.
pause
