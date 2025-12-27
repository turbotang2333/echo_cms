@echo off
chcp 65001 >nul

echo ==========================================
echo   Test Scheduled Task
echo ==========================================
echo.

echo This will run the daily crawl script immediately
echo (same as scheduled task, but manual trigger)
echo.
pause

set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%daily_crawl.bat"

echo.
echo ==========================================
echo   Test Complete
echo ==========================================
echo.
echo Check the log file in logs\ directory
echo.
pause
