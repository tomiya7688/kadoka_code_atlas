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

if exist "config" (
    if not exist "dist\kadoka-code-atlas\config" mkdir "dist\kadoka-code-atlas\config"
    xcopy /E /I /Y "config\*" "dist\kadoka-code-atlas\config\" >nul
    if errorlevel 1 exit /b 1
)

echo.
echo App build completed: dist\kadoka-code-atlas\kadoka-code-atlas.exe
endlocal
