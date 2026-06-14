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
REM Final files:
REM   release\OneSocialInstaller.exe
REM   release\OneSocialApp.zip
REM
REM Notes:
REM   - .spec files are generated inside build\specs, not app root.
REM   - build, dist and release are recreated on each run.
REM   - logs are stored in dist\logs.
REM =========================================================

cd /d "%~dp0"
set "ROOT_DIR=%CD%"

set "APP_NAME=OneSocial"
set "SCHEDULER_NAME=OneSocialScheduler"
set "UNINSTALL_NAME=uninstall"
set "INSTALLER_NAME=OneSocialInstaller"
set "PAYLOAD_ZIP=OneSocialApp.zip"

set "BUILD_DIR=%ROOT_DIR%\build"
set "DIST_DIR=%ROOT_DIR%\dist"
set "RELEASE_DIR=%ROOT_DIR%\release"
set "LOG_DIR=%DIST_DIR%\logs"
set "SPEC_DIR=%BUILD_DIR%\specs"
set "WORK_DIR=%BUILD_DIR%\work"

REM PyInstaller log levels: WARN, ERROR, FATAL
set "PYI_LOG_LEVEL=WARN"

REM Hide SyntaxWarning noise from third-party libraries during build.
set "PYTHONWARNINGS=ignore::SyntaxWarning"

echo.
echo ==========================================
echo OneSocial - Build
echo ==========================================
echo Root: %ROOT_DIR%

REM =========================================================
REM Initial cleanup
REM =========================================================
echo.
echo [INFO] Cleaning previous build folders...

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"

REM Delete loose .spec files that PyInstaller may have left in app root.
del /f /q "%ROOT_DIR%\*.spec" >nul 2>nul

mkdir "%RELEASE_DIR%" >nul 2>nul
mkdir "%LOG_DIR%" >nul 2>nul
mkdir "%SPEC_DIR%" >nul 2>nul
mkdir "%WORK_DIR%" >nul 2>nul

REM =========================================================
REM Basic checks
REM =========================================================
echo [INFO] Checking required files...

where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo [ERROR] PyInstaller is not installed or is not in PATH.
    echo Install it with:
    echo   python -m pip install pyinstaller
    exit /b 1
)

call :require_file "%ROOT_DIR%\main.py"
if errorlevel 1 exit /b 1

call :require_file "%ROOT_DIR%\OneSocialScheduler.py"
if errorlevel 1 exit /b 1

call :require_file "%ROOT_DIR%\uninstaller.py"
if errorlevel 1 exit /b 1

call :require_file "%ROOT_DIR%\installer.py"
if errorlevel 1 exit /b 1

call :require_file "%ROOT_DIR%\web\icons\Kibo.ico"
if errorlevel 1 exit /b 1

call :require_file "%ROOT_DIR%\web\icons\Kibo_calendar.ico"
if errorlevel 1 exit /b 1

call :require_file "%ROOT_DIR%\web\icons\Kibo_uninstaller.ico"
if errorlevel 1 exit /b 1

call :require_file "%ROOT_DIR%\web\icons\Kibo_installer.ico"
if errorlevel 1 exit /b 1

echo [OK] Required files found.

REM =========================================================
REM 1) Build OneSocial.exe
REM =========================================================
echo.
echo [1/5] Building %APP_NAME%.exe...

pyinstaller ^
    --clean ^
    --noconfirm ^
    --log-level=%PYI_LOG_LEVEL% ^
    --distpath "%DIST_DIR%" ^
    --workpath "%WORK_DIR%" ^
    --specpath "%SPEC_DIR%" ^
    --onefile ^
    --noconsole ^
    --name "%APP_NAME%" ^
    --icon "%ROOT_DIR%\web\icons\Kibo.ico" ^
    --add-data "%ROOT_DIR%\web;web" ^
    "%ROOT_DIR%\main.py" > "%LOG_DIR%\%APP_NAME%.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Failed building %APP_NAME%.exe
    call :show_log_tail "%LOG_DIR%\%APP_NAME%.log"
    goto :build_failed
)

call :require_file "%DIST_DIR%\%APP_NAME%.exe"
if errorlevel 1 goto :build_failed

echo [OK] %APP_NAME%.exe built.

REM =========================================================
REM 2) Build OneSocialScheduler.exe
REM =========================================================
echo.
echo [2/5] Building %SCHEDULER_NAME%.exe...

pyinstaller ^
    --clean ^
    --noconfirm ^
    --log-level=%PYI_LOG_LEVEL% ^
    --distpath "%DIST_DIR%" ^
    --workpath "%WORK_DIR%" ^
    --specpath "%SPEC_DIR%" ^
    --onefile ^
    --noconsole ^
    --name "%SCHEDULER_NAME%" ^
    --icon "%ROOT_DIR%\web\icons\Kibo_calendar.ico" ^
    "%ROOT_DIR%\OneSocialScheduler.py" > "%LOG_DIR%\%SCHEDULER_NAME%.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Failed building %SCHEDULER_NAME%.exe
    call :show_log_tail "%LOG_DIR%\%SCHEDULER_NAME%.log"
    goto :build_failed
)

call :require_file "%DIST_DIR%\%SCHEDULER_NAME%.exe"
if errorlevel 1 goto :build_failed

echo [OK] %SCHEDULER_NAME%.exe built.

REM =========================================================
REM 3) Build uninstall.exe
REM IMPORTANT:
REM installer.py expects uninstall.exe, not uninstaller.exe.
REM =========================================================
echo.
echo [3/5] Building %UNINSTALL_NAME%.exe...

pyinstaller ^
    --clean ^
    --noconfirm ^
    --log-level=%PYI_LOG_LEVEL% ^
    --distpath "%DIST_DIR%" ^
    --workpath "%WORK_DIR%" ^
    --specpath "%SPEC_DIR%" ^
    --onefile ^
    --noconsole ^
    --name "%UNINSTALL_NAME%" ^
    --icon "%ROOT_DIR%\web\icons\Kibo_uninstaller.ico" ^
    "%ROOT_DIR%\uninstaller.py" > "%LOG_DIR%\%UNINSTALL_NAME%.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Failed building %UNINSTALL_NAME%.exe
    call :show_log_tail "%LOG_DIR%\%UNINSTALL_NAME%.log"
    goto :build_failed
)

call :require_file "%DIST_DIR%\%UNINSTALL_NAME%.exe"
if errorlevel 1 goto :build_failed

echo [OK] %UNINSTALL_NAME%.exe built.

REM =========================================================
REM 4) Create OneSocialApp.zip with the 3 payload EXEs
REM =========================================================
echo.
echo [4/5] Creating payload %PAYLOAD_ZIP%...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Stop'; Compress-Archive -LiteralPath '%DIST_DIR%\%APP_NAME%.exe','%DIST_DIR%\%SCHEDULER_NAME%.exe','%DIST_DIR%\%UNINSTALL_NAME%.exe' -DestinationPath '%RELEASE_DIR%\%PAYLOAD_ZIP%' -Force" > "%LOG_DIR%\zip.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Failed creating %PAYLOAD_ZIP%
    call :show_log_tail "%LOG_DIR%\zip.log"
    goto :build_failed
)

call :require_file "%RELEASE_DIR%\%PAYLOAD_ZIP%"
if errorlevel 1 goto :build_failed

echo [OK] %PAYLOAD_ZIP% created.

REM =========================================================
REM 5) Build OneSocialInstaller.exe
REM =========================================================
echo.
echo [5/5] Building %INSTALLER_NAME%.exe...

REM The payload ZIP is also added as bundled data.
REM This helps installer.py find it whether it uses sys._MEIPASS or the external release ZIP.
pyinstaller ^
    --clean ^
    --noconfirm ^
    --log-level=%PYI_LOG_LEVEL% ^
    --distpath "%DIST_DIR%" ^
    --workpath "%WORK_DIR%" ^
    --specpath "%SPEC_DIR%" ^
    --onefile ^
    --noconsole ^
    --name "%INSTALLER_NAME%" ^
    --icon "%ROOT_DIR%\web\icons\Kibo_installer.ico" ^
    --add-data "%RELEASE_DIR%\%PAYLOAD_ZIP%;." ^
    "%ROOT_DIR%\installer.py" > "%LOG_DIR%\%INSTALLER_NAME%.log" 2>&1

if errorlevel 1 (
    echo [ERROR] Failed building %INSTALLER_NAME%.exe
    call :show_log_tail "%LOG_DIR%\%INSTALLER_NAME%.log"
    goto :build_failed
)

REM Normal expected output:
set "INSTALLER_OUTPUT=%DIST_DIR%\%INSTALLER_NAME%.exe"

REM Defensive fallback: if PyInstaller places it somewhere unexpected, find it.
if not exist "%INSTALLER_OUTPUT%" (
    set "FOUND_INSTALLER="
    for /r "%DIST_DIR%" %%F in ("%INSTALLER_NAME%.exe") do (
        set "FOUND_INSTALLER=%%~fF"
    )

    if defined FOUND_INSTALLER (
        echo [WARN] Installer was found in an unexpected location:
        echo        !FOUND_INSTALLER!
        set "INSTALLER_OUTPUT=!FOUND_INSTALLER!"
    ) else (
        echo [ERROR] %INSTALLER_NAME%.exe was not found in %DIST_DIR%.
        call :show_log_tail "%LOG_DIR%\%INSTALLER_NAME%.log"
        goto :build_failed
    )
)

copy /Y "%INSTALLER_OUTPUT%" "%RELEASE_DIR%\%INSTALLER_NAME%.exe" >nul
if errorlevel 1 (
    echo [ERROR] Could not copy %INSTALLER_NAME%.exe to release.
    echo Source:
    echo   %INSTALLER_OUTPUT%
    echo Target:
    echo   %RELEASE_DIR%\%INSTALLER_NAME%.exe
    goto :build_failed
)

call :require_file "%RELEASE_DIR%\%INSTALLER_NAME%.exe"
if errorlevel 1 goto :build_failed

echo [OK] %INSTALLER_NAME%.exe built and copied to release.

REM Defensive cleanup: remove loose .spec files from app root.
del /f /q "%ROOT_DIR%\*.spec" >nul 2>nul

REM =========================================================
REM Final verification
REM =========================================================
echo.
echo [INFO] Final release contents:
dir /b "%RELEASE_DIR%"

call :require_file "%RELEASE_DIR%\%INSTALLER_NAME%.exe"
if errorlevel 1 goto :build_failed

call :require_file "%RELEASE_DIR%\%PAYLOAD_ZIP%"
if errorlevel 1 goto :build_failed

echo.
echo ==========================================
echo BUILD COMPLETED
echo ==========================================
echo Deliver these files together:
echo   %RELEASE_DIR%\%INSTALLER_NAME%.exe
echo   %RELEASE_DIR%\%PAYLOAD_ZIP%
echo.
echo Detailed logs:
echo   %LOG_DIR%
echo ==========================================
echo.

exit /b 0

REM =========================================================
REM Subroutines
REM =========================================================

:require_file
if not exist "%~1" (
    echo [ERROR] File not found:
    echo   %~1
    exit /b 1
)
exit /b 0

:show_log_tail
echo.
echo ---------- Last log lines ----------
powershell -NoProfile -Command "if (Test-Path '%~1') { Get-Content '%~1' -Tail 80 } else { Write-Host 'Log not found: %~1' }"
echo ----------------------------------
echo.
exit /b 0

:build_failed
echo.
echo ==========================================
echo BUILD FAILED
echo ==========================================
echo Check logs here:
echo   %LOG_DIR%
echo.
echo Current release contents:
if exist "%RELEASE_DIR%" dir /b "%RELEASE_DIR%"
echo.
echo Current dist contents:
if exist "%DIST_DIR%" dir /b "%DIST_DIR%"
echo ==========================================
echo.
exit /b 1
