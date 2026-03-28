@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: export_all.bat ^<activity.fit^|activity.gpx^> [extra plot_gpx.py args]
    echo Example: export_all.bat 20081725704_ACTIVITY.fit
    echo Example: export_all.bat 20081725704_ACTIVITY.fit --location "Custom Location"
    exit /b 1
)

set "INPUT=%~1"
if not exist "%INPUT%" (
    echo Input file not found: %INPUT%
    exit /b 1
)

set "BASENAME=%~n1"
set "EXTRA_ARGS="

shift

:collect_args
if "%~1"=="" goto run_exports
set "EXTRA_ARGS=!EXTRA_ARGS! "%~1""
shift
goto collect_args

:run_exports
call :render_template story_overlay solid
if errorlevel 1 exit /b 1

call :render_template clean_card gradient
if errorlevel 1 exit /b 1

call :render_template glass_slab solid
if errorlevel 1 exit /b 1

call :render_template clipboard_card solid
if errorlevel 1 exit /b 1

call :render_template neon_split solid
if errorlevel 1 exit /b 1

echo All exports saved under exports\
exit /b 0

:render_template
set "TEMPLATE=%~1"
set "MODE=%~2"
set "OUTPUT=exports\%TEMPLATE%_%BASENAME%.png"
echo Rendering %TEMPLATE%...
python plot_gpx.py --input "%INPUT%" --template "%TEMPLATE%" --mode "%MODE%" --output "%OUTPUT%" !EXTRA_ARGS!
if errorlevel 1 (
    echo Export failed for %TEMPLATE%.
    exit /b 1
)
exit /b 0
