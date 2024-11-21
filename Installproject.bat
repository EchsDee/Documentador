@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo ================================
echo Starting Installation Process
echo ================================
echo.

:: Function to check if a command exists
where_exists() {
    where /Q "%~1"
}

:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Installing Python...
    
    :: Define Python installer URL for Python 3.12.0
    set PYTHON_URL=https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe
    
    :: Define installer path
    set PYTHON_INSTALLER=%TEMP%\python-installer.exe
    
    :: Download Python installer using PowerShell
    echo Downloading Python installer...
    powershell -Command "Invoke-WebRequest -Uri %PYTHON_URL% -OutFile %PYTHON_INSTALLER%"
    
    :: Run Python installer silently and add Python to PATH
    echo Installing Python...
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
    
    :: Verify installation
    echo Verifying Python installation...
    python --version >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo Python installation failed. Please install Python manually.
        EXIT /B 1
    ) ELSE (
        echo Python installed successfully.
    )
) ELSE (
    echo Python is already installed.
)

echo.
echo Creating virtual environment...
:: Create virtual environment named 'venv'
python -m venv venv

echo Activating virtual environment...
:: Activate the virtual environment
CALL venv\Scripts\activate.bat

echo.
echo Upgrading pip...
:: Upgrade pip to the latest version
python -m pip install --upgrade pip

echo.
echo Installing Python dependencies...
:: Install required Python packages
pip install flask python-docx waitress requests apscheduler werkzeug pywin32

echo.
echo Installing pywin32 post-install scripts...
:: Run pywin32 post-install
python -m pywin32_postinstall -install

echo.
echo Installing service...
:: Install the Windows service
python DocumentadorService.py install

echo.
echo Starting the service...
:: Start the service
python DocumentadorService.py start

echo.
echo Installation and setup completed successfully!
echo You can access the application at http://localhost:8000
ENDLOCAL
pause