@echo off
chcp 65001 >nul

REM ==================== Daily Crawl Script ====================
REM This script is called by Windows Task Scheduler
REM Runs crawler, commits and pushes to GitHub

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%..\..\"
cd /d "%PROJECT_DIR%"

REM Generate log filename
for /f "usebackq" %%i in (`powershell -Command "Get-Date -Format 'yyyyMMdd'"`) do set datestr=%%i
set "LOG_FILE=%PROJECT_DIR%\logs\crawl_%datestr%.log"

REM Create logs directory
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

REM Log start
echo ======================================== >> "%LOG_FILE%"
echo Start: %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

REM Run crawler
py -u "%PROJECT_DIR%\crawler\main.py" >> "%LOG_FILE%" 2>&1

if %errorlevel% equ 0 (
    echo Crawler success >> "%LOG_FILE%"
    
    REM Git operations
    cd /d "%PROJECT_DIR%"
    git add public/data.json archive/ >> "%LOG_FILE%" 2>&1
    git commit -m "data: daily update %date%" >> "%LOG_FILE%" 2>&1
    
    if %errorlevel% equ 0 (
        git pull --rebase >> "%LOG_FILE%" 2>&1
        
        REM Handle conflicts
        if %errorlevel% neq 0 (
            git checkout --ours public/data.json >> "%LOG_FILE%" 2>&1
            git checkout --ours archive/ >> "%LOG_FILE%" 2>&1
            git add public/data.json archive/ >> "%LOG_FILE%" 2>&1
            echo | git rebase --continue >> "%LOG_FILE%" 2>&1
        )
        
        git push >> "%LOG_FILE%" 2>&1
        echo Push success >> "%LOG_FILE%"
    ) else (
        echo No changes >> "%LOG_FILE%"
    )
) else (
    echo Crawler failed >> "%LOG_FILE%"
)

REM Log end
echo End: %date% %time% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
