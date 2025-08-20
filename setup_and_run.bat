@echo off
SETLOCAL

REM Determine project directory
set SCRIPT_DIR=%~dp0

REM Check for Python
python --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not detected. Installing Python...
    powershell -Command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile '%SCRIPT_DIR%python-installer.exe'"
    "%SCRIPT_DIR%python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del "%SCRIPT_DIR%python-installer.exe"
    set "PYTHON_HOME=%ProgramFiles%\Python311"
    setx PATH "%PATH%;%PYTHON_HOME%;%PYTHON_HOME%\Scripts" >NUL
    set "PATH=%PATH%;%PYTHON_HOME%;%PYTHON_HOME%\Scripts"
)

REM Upgrade packaging tools
python -m pip install --upgrade pip wheel

REM Build wheels and install requirements
python -m pip wheel -r "%SCRIPT_DIR%requirements.txt" -w "%SCRIPT_DIR%wheelhouse"
python -m pip install --no-index --find-links="%SCRIPT_DIR%wheelhouse" -r "%SCRIPT_DIR%requirements.txt"

REM Launch the application
python "%SCRIPT_DIR%YBS_CONTROL.py"
ENDLOCAL
