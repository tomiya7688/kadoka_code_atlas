@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

%PYTHON% -m pip install --upgrade pyinstaller
if errorlevel 1 exit /b 1

%PYTHON% -m PyInstaller --onefile --clean --name kadoka-code-atlas app.py
if errorlevel 1 exit /b 1

echo.
echo EXE build completed: dist\kadoka-code-atlas.exe
endlocal