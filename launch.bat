@echo off
setlocal
title SteamSeparator

cd /d "%~dp0"

:: 1. Check LOCALAPPDATA Python 3.12 installation first
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" run.py
    goto :end
)

:: 2. Check py launcher
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py -3 run.py
    goto :end
)

:: 3. Check generic python on PATH
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python run.py
    goto :end
)

echo FEHLER: Kein funktionierendes Python gefunden!
echo Bitte installiere Python 3.10+ oder starte run.py direkt.
pause

:end
