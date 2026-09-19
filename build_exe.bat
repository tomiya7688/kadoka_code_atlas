@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

where dotnet >nul 2>nul
if errorlevel 1 (
    echo .NET SDK 10 is required to build the bundled C# Roslyn backend.
    exit /b 1
)

if exist "backends\csharp" rmdir /S /Q "backends\csharp"
dotnet publish "backend-src\csharp\Kadoka.CSharp.Backend.csproj" -c Release -r win-x64 --self-contained true -p:PublishSingleFile=false -p:PublishTrimmed=false -o "backends\csharp"
if errorlevel 1 exit /b 1

%PYTHON% -m pip install -e ".[exe]"
if errorlevel 1 exit /b 1

%PYTHON% -m PyInstaller --onedir --clean --name kadoka-code-atlas -y app.py
if errorlevel 1 exit /b 1

if exist "config" (
    if not exist "dist\kadoka-code-atlas\config" mkdir "dist\kadoka-code-atlas\config"
    xcopy /E /I /Y "config\*" "dist\kadoka-code-atlas\config\" >nul
    if errorlevel 1 exit /b 1
)

if exist "backends" (
    if not exist "dist\kadoka-code-atlas\backends" mkdir "dist\kadoka-code-atlas\backends"
    xcopy /E /I /Y "backends\*" "dist\kadoka-code-atlas\backends\" >nul
    if errorlevel 1 exit /b 1
)

echo.
echo App build completed: dist\kadoka-code-atlas\kadoka-code-atlas.exe
endlocal
