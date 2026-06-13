@echo off
setlocal
rem Runs one AI Bureau publication pass in the configured WSL environment.
wsl.exe --cd "%~dp0" python3 -m publisher --env-file actual.env
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Publisher failed with exit code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
