@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

%PYTHON% -m pip install -e ".[exe]"
if errorlevel 1 exit /b 1

%PYTHON% -m PyInstaller --onedir --clean --name kadoka-code-atlas -y app.py
if errorlevel 1 exit /b 1

if exist "kadoka-code-atlas.example.json" (
    copy /Y "kadoka-code-atlas.example.json" "dist\kadoka-code-atlas\kadoka-code-atlas.example.json" >nul
    if errorlevel 1 exit /b 1
)

echo.
echo App build completed: dist\kadoka-code-atlas\kadoka-code-atlas.exe
endlocal
