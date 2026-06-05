@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =========================================================
REM OneSocial - Build script
REM Compila la app, scheduler, desinstalador, arma el payload ZIP
REM y deja el instalador final junto al ZIP en la carpeta release.
REM =========================================================

cd /d "%~dp0"

set "APP_NAME=OneSocial"
set "SCHEDULER_NAME=OneSocialScheduler"
set "UNINSTALL_NAME=uninstall"
set "INSTALLER_NAME=OneSocialInstaller"
set "PAYLOAD_ZIP=OneSocialApp.zip"
set "RELEASE_DIR=release"

REM ---- Limpieza inicial ----
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%"

REM ---- Verificaciones basicas ----
where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller no esta instalado o no esta en PATH.
    echo Instalar con: python -m pip install pyinstaller
    exit /b 1
)

if not exist main.py (
    echo [ERROR] No se encontro main.py
    exit /b 1
)

if not exist OneSocialScheduler.py (
    echo [ERROR] No se encontro OneSocialScheduler.py
    exit /b 1
)

if not exist uninstaller.py (
    echo [ERROR] No se encontro uninstaller.py
    exit /b 1
)

if not exist installer.py (
    echo [ERROR] No se encontro installer.py
    exit /b 1
)

REM =========================================================
REM 1) Compilar OneSocial.exe
REM =========================================================
echo.
echo [1/5] Compilando %APP_NAME%.exe...
pyinstaller --clean --onefile --noconsole --name "%APP_NAME%" --icon="web/icons/Kibo.ico" --add-data "web;web" main.py
if errorlevel 1 goto :build_failed

REM =========================================================
REM 2) Compilar OneSocialScheduler.exe
REM =========================================================
echo.
echo [2/5] Compilando %SCHEDULER_NAME%.exe...
pyinstaller --clean --onefile --noconsole --name "%SCHEDULER_NAME%" --icon="web/icons/Kibo_calendar.ico" OneSocialScheduler.py
if errorlevel 1 goto :build_failed

REM =========================================================
REM 3) Compilar uninstall.exe
REM IMPORTANTE: el installer.py espera uninstall.exe, NO uninstaller.exe.
REM =========================================================
echo.
echo [3/5] Compilando %UNINSTALL_NAME%.exe...
pyinstaller --clean --onefile --noconsole --name "%UNINSTALL_NAME%" --icon="web/icons/Kibo_uninstaller.ico" uninstaller.py
if errorlevel 1 goto :build_failed

REM ---- Validar outputs del payload ----
if not exist "dist\%APP_NAME%.exe" (
    echo [ERROR] Falta dist\%APP_NAME%.exe
    exit /b 1
)
if not exist "dist\%SCHEDULER_NAME%.exe" (
    echo [ERROR] Falta dist\%SCHEDULER_NAME%.exe
    exit /b 1
)
if not exist "dist\%UNINSTALL_NAME%.exe" (
    echo [ERROR] Falta dist\%UNINSTALL_NAME%.exe
    exit /b 1
)

REM =========================================================
REM 4) Crear OneSocialApp.zip con los 3 EXE requeridos
REM =========================================================
echo.
echo [4/5] Creando payload %PAYLOAD_ZIP%...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'dist\%APP_NAME%.exe','dist\%SCHEDULER_NAME%.exe','dist\%UNINSTALL_NAME%.exe' -DestinationPath '%RELEASE_DIR%\%PAYLOAD_ZIP%' -Force"
if errorlevel 1 goto :build_failed

REM =========================================================
REM 5) Compilar OneSocialInstaller.exe
REM =========================================================
echo.
echo [5/5] Compilando %INSTALLER_NAME%.exe...
pyinstaller --clean --onefile --noconsole --name "%INSTALLER_NAME%" --icon="web/icons/Kibo_installer.ico" installer.py
if errorlevel 1 goto :build_failed

if not exist "dist\%INSTALLER_NAME%.exe" (
    echo [ERROR] Falta dist\%INSTALLER_NAME%.exe
    exit /b 1
)

copy /Y "dist\%INSTALLER_NAME%.exe" "%RELEASE_DIR%\%INSTALLER_NAME%.exe" >nul

REM ---- Ver final ----
echo.
echo ==========================================
echo BUILD COMPLETADO

echo Entregar juntos estos archivos:
echo   %RELEASE_DIR%\%INSTALLER_NAME%.exe
echo   %RELEASE_DIR%\%PAYLOAD_ZIP%
echo ==========================================
echo.
exit /b 0

:build_failed
echo.
echo [ERROR] Fallo la compilacion. Revisa el mensaje anterior.
exit /b 1
