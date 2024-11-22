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

ECHO Checking if Documentador Service is installed...

sc query "DocumentadorService" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Documentador Service is not installed.
) ELSE (
    ECHO Stopping Documentador Service...
    sc stop "DocumentadorService"
    
    ECHO Deleting Documentador Service...
    sc delete "DocumentadorService"
    
    ECHO Service stopped and removed successfully.
)

PAUSE