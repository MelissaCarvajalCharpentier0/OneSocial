@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =========================================================
REM OneSocial - Build script
REM Compiles:
REM   1) OneSocial.exe
REM   2) OneSocialScheduler.exe
REM   3) uninstall.exe
REM   4) OneSocialApp.zip
REM   5) OneSocialInstaller.exe
REM
REM Product on release/
REM Logs stored on dist/
REM =========================================================

cd /d "%~dp0"

set "APP_NAME=OneSocial"
set "SCHEDULER_NAME=OneSocialScheduler"
set "UNINSTALL_NAME=uninstall"
set "INSTALLER_NAME=OneSocialInstaller"
set "PAYLOAD_ZIP=OneSocialApp.zip"
set "RELEASE_DIR=release"
set "DIST_DIR=dist"
set "LOG_DIR=%DIST_DIR%"

REM PyInstaller
REM Niveles utiles: WARN, ERROR, FATAL
set "PYI_LOG_LEVEL=WARN"

REM Oculta SyntaxWarning de bibliotecas externas durante el build.
set "PYTHONWARNINGS=ignore::SyntaxWarning"

REM Comando base de PyInstaller.
REM --noconfirm evita preguntas interactivas.
REM --distpath, --workpath y --specpath mantienen ordenadas las carpetas.
set "PYI_COMMON=pyinstaller --clean --noconfirm --log-level=%PYI_LOG_LEVEL% --distpath dist --workpath build\work"

echo.
echo ==========================================
echo OneSocial - Build
echo ==========================================

REM =========================================================
REM Limpieza inicial
REM =========================================================
echo.
echo [INFO] Limpiando carpetas anteriores...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"

mkdir "%RELEASE_DIR%" >nul 2>nul
mkdir "%LOG_DIR%" >nul 2>nul
mkdir "build\specs" >nul 2>nul
mkdir "build\work" >nul 2>nul

REM =========================================================
REM Verificaciones basicas
REM =========================================================
echo [INFO] Verificando archivos requeridos...

where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller no esta instalado o no esta en PATH.
    echo Instalar con:
    echo   python -m pip install pyinstaller
    exit /b 1
)

call :require_file "main.py"
if errorlevel 1 exit /b 1

call :require_file "OneSocialScheduler.py"
if errorlevel 1 exit /b 1

call :require_file "uninstaller.py"
if errorlevel 1 exit /b 1

call :require_file "installer.py"
if errorlevel 1 exit /b 1

call :require_file "web\icons\Kibo.ico"
if errorlevel 1 exit /b 1

call :require_file "web\icons\Kibo_calendar.ico"
if errorlevel 1 exit /b 1

call :require_file "web\icons\Kibo_uninstaller.ico"
if errorlevel 1 exit /b 1

call :require_file "web\icons\Kibo_installer.ico"
if errorlevel 1 exit /b 1

echo [OK] Verificaciones completadas.

REM =========================================================
REM 1) Compilar OneSocial.exe
REM =========================================================
echo.
echo [1/5] Compilando %APP_NAME%.exe...

%PYI_COMMON% ^
    --onefile ^
    --noconsole ^
    --name "%APP_NAME%" ^
    --icon="web/icons/Kibo.ico" ^
    --add-data "web;web" ^
    main.py > "%LOG_DIR%\%APP_NAME%.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Fallo compilando %APP_NAME%.exe
    call :show_log_tail "%LOG_DIR%\%APP_NAME%.log"
    goto :build_failed
)

echo [OK] %APP_NAME%.exe compilado.

REM =========================================================
REM 2) Compilar OneSocialScheduler.exe
REM =========================================================
echo.
echo [2/5] Compilando %SCHEDULER_NAME%.exe...

%PYI_COMMON% ^
    --onefile ^
    --noconsole ^
    --name "%SCHEDULER_NAME%" ^
    --icon="web/icons/Kibo_calendar.ico" ^
    OneSocialScheduler.py > "%LOG_DIR%\%SCHEDULER_NAME%.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Fallo compilando %SCHEDULER_NAME%.exe
    call :show_log_tail "%LOG_DIR%\%SCHEDULER_NAME%.log"
    goto :build_failed
)

echo [OK] %SCHEDULER_NAME%.exe compilado.

REM =========================================================
REM 3) Compilar uninstall.exe
REM IMPORTANTE:
REM installer.py espera uninstall.exe, NO uninstaller.exe.
REM =========================================================
echo.
echo [3/5] Compilando %UNINSTALL_NAME%.exe...

%PYI_COMMON% ^
    --onefile ^
    --noconsole ^
    --name "%UNINSTALL_NAME%" ^
    --icon="web/icons/Kibo_uninstaller.ico" ^
    uninstaller.py > "%LOG_DIR%\%UNINSTALL_NAME%.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Fallo compilando %UNINSTALL_NAME%.exe
    call :show_log_tail "%LOG_DIR%\%UNINSTALL_NAME%.log"
    goto :build_failed
)

echo [OK] %UNINSTALL_NAME%.exe compilado.

REM =========================================================
REM Validar outputs del payload
REM =========================================================
echo.
echo [INFO] Validando archivos generados...

call :require_file "dist\%APP_NAME%.exe"
if errorlevel 1 goto :build_failed

call :require_file "dist\%SCHEDULER_NAME%.exe"
if errorlevel 1 goto :build_failed

call :require_file "dist\%UNINSTALL_NAME%.exe"
if errorlevel 1 goto :build_failed

echo [OK] Outputs del payload encontrados.

REM =========================================================
REM 4) Crear OneSocialApp.zip con los 3 EXE requeridos
REM =========================================================
echo.
echo [4/5] Creando payload %PAYLOAD_ZIP%...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'dist\%APP_NAME%.exe','dist\%SCHEDULER_NAME%.exe','dist\%UNINSTALL_NAME%.exe' -DestinationPath '%RELEASE_DIR%\%PAYLOAD_ZIP%' -Force" > "%LOG_DIR%\zip.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Fallo creando %PAYLOAD_ZIP%
    call :show_log_tail "%LOG_DIR%\zip.log"
    goto :build_failed
)

call :require_file "%RELEASE_DIR%\%PAYLOAD_ZIP%"
if errorlevel 1 goto :build_failed

echo [OK] %PAYLOAD_ZIP% creado.

REM =========================================================
REM 5) Compilar OneSocialInstaller.exe
REM =========================================================
echo.
echo [5/5] Compilando %INSTALLER_NAME%.exe...

%PYI_COMMON% ^
    --onefile ^
    --noconsole ^
    --name "%INSTALLER_NAME%" ^
    --icon="web/icons/Kibo_installer.ico" ^
    installer.py > "%LOG_DIR%\%INSTALLER_NAME%.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Fallo compilando %INSTALLER_NAME%.exe
    call :show_log_tail "%LOG_DIR%\%INSTALLER_NAME%.log"
    goto :build_failed
)

call :require_file "dist\%INSTALLER_NAME%.exe"
if errorlevel 1 goto :build_failed

copy /Y "dist\%INSTALLER_NAME%.exe" "%RELEASE_DIR%\%INSTALLER_NAME%.exe" >nul
if errorlevel 1 (
    echo [ERROR] No se pudo copiar %INSTALLER_NAME%.exe a %RELEASE_DIR%.
    goto :build_failed
)

echo [OK] %INSTALLER_NAME%.exe compilado.

REM =========================================================
REM Final
REM =========================================================
echo.
echo ==========================================
echo BUILD COMPLETADO
echo ==========================================
echo Entregar juntos estos archivos:
echo   %RELEASE_DIR%\%INSTALLER_NAME%.exe
echo   %RELEASE_DIR%\%PAYLOAD_ZIP%
echo.
echo Logs detallados:
echo   %LOG_DIR%
echo ==========================================
echo.

exit /b 0

REM =========================================================
REM Subrutinas
REM =========================================================

:require_file
if not exist "%~1" (
    echo [ERROR] No se encontro: %~1
    exit /b 1
)
exit /b 0

:show_log_tail
echo.
echo ---------- Ultimas lineas del log ----------
powershell -NoProfile -Command "if (Test-Path '%~1') { Get-Content '%~1' -Tail 80 } else { Write-Host 'No se encontro el log: %~1' }"
echo --------------------------------------------
echo.
exit /b 0

:build_failed
echo.
echo ==========================================
echo BUILD FALLIDO
echo ==========================================
echo Revisa los logs en:
echo   %LOG_DIR%
echo ==========================================
echo.
exit /b 1