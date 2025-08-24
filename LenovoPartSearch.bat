@echo off
:: Lenovo Part Search - Quick Launch for Windows
:: This file can be placed on desktop for one-click startup

title Lenovo Part Search

echo ========================================
echo    Lenovo Part Search - Multi-File
echo ========================================
echo.
echo Starting application via WSL...
echo.

:: Check if WSL is installed
wsl --status >nul 2>&1
if errorlevel 1 (
    echo ERROR: WSL is not installed or not available.
    echo Please install WSL first: wsl --install
    pause
    exit /b 1
)

:: Get the default WSL distribution
for /f "tokens=1" %%i in ('wsl -l -q ^| findstr /r "^[a-zA-Z]" ^| head -1') do set WSL_DISTRO=%%i

:: If no default distro found, try Ubuntu
if "%WSL_DISTRO%"=="" set WSL_DISTRO=Ubuntu

:: Launch the application
echo Using WSL distribution: %WSL_DISTRO%
echo.

:: Open browser after a delay (give server time to start)
start /min cmd /c "timeout /t 3 >nul && start http://localhost:8080"

:: Run the quick start script in WSL
wsl -d %WSL_DISTRO% bash -c "cd /mnt/c/projects/lenovo-pricing && chmod +x quick_start.sh 2>/dev/null; ./quick_start.sh"

:: If the above fails, try without specifying distribution
if errorlevel 1 (
    echo.
    echo Trying alternative launch method...
    wsl bash -c "cd /mnt/c/projects/lenovo-pricing && chmod +x quick_start.sh 2>/dev/null; ./quick_start.sh"
)

pause