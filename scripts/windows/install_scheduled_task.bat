@echo off
chcp 65001 >nul

echo ==========================================
echo   Install Windows Scheduled Task
echo ==========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%..\..\"
cd /d "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"

echo Project: %PROJECT_DIR%
echo.
echo This will create a scheduled task:
echo   - Task Name: EchoCMS_DailyCrawl
echo   - Schedule: Daily at 9:00 AM
echo   - Script: daily_crawl.bat
echo.
echo Note: Computer must be powered on at 9:00 AM
echo.
pause

REM Delete existing task if exists
schtasks /delete /tn "EchoCMS_DailyCrawl" /f >nul 2>&1

REM Create new scheduled task
schtasks /create /tn "EchoCMS_DailyCrawl" /tr "\"%PROJECT_DIR%\scripts\windows\daily_crawl.bat\"" /sc daily /st 09:00 /f

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo   SUCCESS!
    echo ==========================================
    echo.
    echo Task created successfully!
    echo.
    echo Details:
    echo   Name: EchoCMS_DailyCrawl
    echo   Schedule: Every day at 9:00 AM
    echo   Script: %PROJECT_DIR%\scripts\windows\daily_crawl.bat
    echo   Logs: %PROJECT_DIR%\logs\crawl_YYYYMMDD.log
    echo.
    echo Useful commands:
    echo   View task: schtasks /query /tn "EchoCMS_DailyCrawl" /v
    echo   Run now: schtasks /run /tn "EchoCMS_DailyCrawl"
    echo   Delete: schtasks /delete /tn "EchoCMS_DailyCrawl" /f
    echo.
) else (
    echo.
    echo ==========================================
    echo   FAILED!
    echo ==========================================
    echo.
    echo Failed to create scheduled task
    echo.
    echo Possible reasons:
    echo   1. Need Administrator privileges
    echo   2. Task Scheduler service not running
    echo.
    echo Solution:
    echo   Right-click this file and select "Run as administrator"
    echo.
)

pause

