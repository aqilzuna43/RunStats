@echo off
setlocal
setlocal EnableDelayedExpansion

cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: export_glass.bat ^<activity.fit^|activity.gpx^> [extra plot_gpx.py args]
    echo Example: export_glass.bat 20081725704_ACTIVITY.fit
    echo Example: export_glass.bat 20081725704_ACTIVITY.fit --location "Suzhou Industrial Park"
    exit /b 1
)

set "INPUT=%~1"
if not exist "%INPUT%" (
    echo Input file not found: %INPUT%
    exit /b 1
)

set "BASENAME=%~n1"
set "OUTPUT=exports\glass_slab_%BASENAME%.png"

shift
set "EXTRA_ARGS="

:collect_args
if "%~1"=="" goto run_export
set "EXTRA_ARGS=!EXTRA_ARGS! "%~1""
shift
goto collect_args

:run_export
python plot_gpx.py --input "%INPUT%" --template glass_slab --mode solid --output "%OUTPUT%" !EXTRA_ARGS!
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    echo Export failed.
    exit /b %EXITCODE%
)

echo Export saved to %OUTPUT%
exit /b 0
