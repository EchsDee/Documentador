@echo off
CLS

:: Check for Administrator privileges
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO This script requires administrative privileges.
    ECHO Please run as administrator.
    PAUSE
    EXIT /B
)

:: Get the directory of the batch script
SET "SCRIPT_DIR=%~dp0"

:: Create DocumentadorService directory if it doesn't exist
IF NOT EXIST "C:\DocumentadorService" (
    MKDIR "C:\DocumentadorService"
    ECHO Created directory C:\DocumentadorService
)

ECHO Checking if Documentador Service is already installed...

sc query "DocumentadorService" >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    ECHO Documentador Service is already installed.
) ELSE (
    ECHO Installing Documentador Service...
    python "%SCRIPT_DIR%DocumentadorService.py" install

    ECHO Starting Documentador Service...
    python "%SCRIPT_DIR%DocumentadorService.py" start

    ECHO Service installed and started successfully.
)

PAUSE