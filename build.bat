@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf8

:menu
cls
echo ===================================================
echo               ANY CONVERTER BUILD TOOLS            
echo ===================================================
echo.
echo Please select a build option:
echo 1. Build Standalone Portable Executable (EXE)
echo 2. Build Windows Installer Package (MSIX)
echo 3. Update Application Version
echo 4. Exit
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto build_exe
if "%choice%"=="2" goto build_msix
if "%choice%"=="3" goto update_version
if "%choice%"=="4" goto end

goto menu

:build_exe
echo.
echo ===================================================
echo [1/1] Packaging Standalone Executable...
echo ===================================================
set "FLET_VIEW_PATH=%CD%\.flet_view"
python scripts\custom_pack.py main.py -y --name "AnyConverterApp" --icon assets\icon.ico --add-data "assets;assets" --add-data "bin;bin" --distpath "dist" --product-name "Any Converter" --file-description "Any Converter" --product-version "1.1.0.0" --file-version "1.1.0.0" --company-name "SwiftGrab" --copyright "Copyright (c) 2026 SwiftGrab"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    goto menu
)
echo.
echo [SUCCESS] Executable built successfully in "dist\AnyConverterApp.exe"
pause
goto menu

:build_msix
echo.
echo ===================================================
echo [1/2] Packaging Executable...
echo ===================================================
set "FLET_VIEW_PATH=%CD%\.flet_view"
python scripts\custom_pack.py main.py -y --name "AnyConverterApp" --icon assets\icon.ico --add-data "assets;assets" --add-data "bin;bin" --distpath "dist" --product-name "Any Converter" --file-description "Any Converter" --product-version "1.1.0.0" --file-version "1.1.0.0" --company-name "SwiftGrab" --copyright "Copyright (c) 2026 SwiftGrab"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Flet pack failed.
    pause
    goto menu
)

echo.
echo ===================================================
echo [2/2] Packaging and Signing MSIX...
echo ===================================================
powershell -ExecutionPolicy Bypass -File scripts\build_msix.ps1

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] MSIX packaging failed.
    pause
    goto menu
)

echo.
echo [SUCCESS] MSIX package built in "dist\AnyConverter.msix"
pause
goto menu

:update_version
echo.
set /p new_version="Enter new version (e.g. 1.1.0 or 2.0.0): "
python scripts\update_version.py %new_version%
echo.
pause
goto menu

:end
exit /b 0
