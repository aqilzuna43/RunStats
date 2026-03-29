@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

set "EXTRA_ARGS="

if "%~1"=="" goto run_all_inputs

set "INPUT=%~1"
if not exist "%INPUT%" (
    echo Input file not found: %INPUT%
    exit /b 1
)

shift

:collect_args
if "%~1"=="" goto run_single_input
set "EXTRA_ARGS=!EXTRA_ARGS! "%~1""
shift
goto collect_args

:run_single_input
call :render_for_input "%INPUT%"
if errorlevel 1 exit /b 1
echo All exports saved under exports\
exit /b 0

:run_all_inputs
set "FOUND_INPUT="

for %%F in (*.fit) do (
    if exist "%%~fF" (
        set "FOUND_INPUT=1"
        call :render_for_input "%%~fF"
        if errorlevel 1 exit /b 1
    )
)

for %%F in (*.gpx) do (
    if exist "%%~fF" (
        set "FOUND_INPUT=1"
        call :render_for_input "%%~fF"
        if errorlevel 1 exit /b 1
    )
)

if not defined FOUND_INPUT (
    echo No .fit or .gpx files found in %~dp0
    exit /b 1
)

echo All exports saved under exports\
exit /b 0

:render_for_input
set "INPUT=%~1"
set "BASENAME=%~n1"
echo.
echo Processing %~nx1...
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

call :render_template kinetic_glass solid
if errorlevel 1 exit /b 1

call :render_template neon_data_story solid
if errorlevel 1 exit /b 1

exit /b 0

:render_template
set "TEMPLATE=%~1"
set "MODE=%~2"
set "OUTPUT=exports\%TEMPLATE%_%BASENAME%.png"
echo Rendering %TEMPLATE% for %BASENAME%...
python plot_gpx.py --input "%INPUT%" --template "%TEMPLATE%" --mode "%MODE%" --output "%OUTPUT%" !EXTRA_ARGS!
if errorlevel 1 (
    echo Export failed for %TEMPLATE%.
    exit /b 1
)
exit /b 0
