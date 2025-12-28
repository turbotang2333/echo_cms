@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ==================== Configuration ====================
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%..\..\"
cd /d "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"

set "GITHUB_ACTIONS_URL=https://github.com/turbotang2333/echo_cms/actions"
set "WEBSITE_URL=https://turbotang2333.github.io/echo_cms/"

REM Create logs directory and log file
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"
for /f "delims=" %%i in ('powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set "DATETIME=%%i"
set "LOG_FILE=%PROJECT_DIR%\logs\daily_crawl_%DATETIME%.log"

REM Check if running interactively (has parameter "test" or "manual")
set "INTERACTIVE=0"
if /i "%~1"=="test" set "INTERACTIVE=1"
if /i "%~1"=="manual" set "INTERACTIVE=1"

REM ==================== Helper Function ====================
goto :main

:log
if "%~1"=="" (
    echo.
    echo. >> "%LOG_FILE%"
) else (
    echo %~1
    echo %~1 >> "%LOG_FILE%"
)
goto :eof

:log_cmd
echo.
echo ^> %~1
echo. >> "%LOG_FILE%"
echo ^> %~1 >> "%LOG_FILE%"
goto :eof

REM ==================== Main Process ====================
:main
if "%INTERACTIVE%"=="1" cls

call :log "=========================================="
call :log "  Crawler System - Daily Update"
call :log "=========================================="
call :log ""
call :log "[INFO] Time: %date% %time:~0,8%"
call :log "[INFO] Path: %PROJECT_DIR%"
call :log "[INFO] Log:  %LOG_FILE%"
call :log "[INFO] Mode: %~1"
call :log ""

REM ==================== Check Environment ====================
call :log "=========================================="
call :log "  Environment Check"
call :log "=========================================="

REM Check Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    call :log "[ERROR] Git not found"
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)
call :log "[OK] Git found"

REM Check Python
set "PYTHON_CMD="
where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
    )
)
if not defined PYTHON_CMD (
    call :log "[ERROR] Python not found"
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)
call :log "[OK] Python found: %PYTHON_CMD%"

REM Check branch
for /f "tokens=*" %%i in ('git branch --show-current') do set "CURRENT_BRANCH=%%i"
call :log "[INFO] Current branch: %CURRENT_BRANCH%"

if not "%CURRENT_BRANCH%"=="main" (
    call :log "[WARNING] Not on main branch, switching..."
    git checkout main >> "%LOG_FILE%" 2>&1
    if %errorlevel% neq 0 (
        call :log "[ERROR] Failed to switch to main branch"
        if "%INTERACTIVE%"=="1" pause
        exit /b 1
    )
    call :log "[OK] Switched to main"
)
call :log ""

REM ==================== Step 1: Run Crawler ====================
call :log "=========================================="
call :log "  Step 1/4: Running Crawler"
call :log "=========================================="
call :log ""

set PYTHONIOENCODING=utf-8
set "CRAWLER_LOG=%PROJECT_DIR%\logs\crawler_temp.log"

REM Run crawler
%PYTHON_CMD% -u "%PROJECT_DIR%\crawler\main.py" > "%CRAWLER_LOG%" 2>&1
set CRAWLER_EXIT=%errorlevel%

REM Display and append to main log
type "%CRAWLER_LOG%"
type "%CRAWLER_LOG%" >> "%LOG_FILE%"

if %CRAWLER_EXIT% neq 0 (
    call :log ""
    call :log "[FAILED] Crawler execution failed"
    call :log "[INFO] See log: %LOG_FILE%"
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)

call :log ""
call :log "[OK] Crawler completed"
call :log ""

REM ==================== Step 2: Check Changes ====================
call :log "=========================================="
call :log "  Step 2/4: Checking Changes"
call :log "=========================================="

git diff --quiet public/data.json archive/
if %errorlevel% equ 0 (
    call :log "[INFO] No data changes detected"
    call :log "[INFO] Nothing to push"
    call :log ""
    if "%INTERACTIVE%"=="1" pause
    exit /b 0
)

call :log "[OK] Data changes detected"
call :log ""

REM ==================== Step 3: Commit and Push ====================
call :log "=========================================="
call :log "  Step 3/4: Commit and Push"
call :log "=========================================="

REM Add data files only
call :log_cmd "git add public/data.json archive/"
git add public/data.json archive/ >> "%LOG_FILE%" 2>&1

for /f "delims=" %%i in ('powershell -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"') do set "COMMIT_TIME=%%i"
call :log_cmd "git commit -m ""data: daily update %COMMIT_TIME%"""
git commit -m "data: daily update %COMMIT_TIME%" >> "%LOG_FILE%" 2>&1

if %errorlevel% neq 0 (
    call :log "[WARNING] No new commits to push"
    if "%INTERACTIVE%"=="1" pause
    exit /b 0
)
call :log "[OK] Commit created"

REM Pull with rebase
call :log_cmd "git pull --rebase"
git pull --rebase >> "%LOG_FILE%" 2>&1
if %errorlevel% neq 0 (
    call :log "[WARNING] Rebase conflict, resolving..."
    git checkout --ours public/data.json 2>nul
    git checkout --ours archive/ 2>nul
    git add public/data.json archive/
    echo | git rebase --continue >> "%LOG_FILE%" 2>&1
)
call :log "[OK] Pull completed"

REM Push
call :log_cmd "git push"
git push >> "%LOG_FILE%" 2>&1
set PUSH_EXIT=%errorlevel%

if %PUSH_EXIT% equ 0 (
    call :log "[OK] Push completed successfully"
) else (
    call :log "[ERROR] Push failed (exit code: %PUSH_EXIT%)"
    call :log "[INFO] See log for details: %LOG_FILE%"
    call :log ""
    call :log "Common issues:"
    call :log "  - Network connection problem"
    call :log "  - Git credentials expired"
    call :log "  - Remote has newer commits"
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)
call :log ""

REM ==================== Step 4: Deployment Status ====================
call :log "=========================================="
call :log "  Step 4/4: Deployment Status"
call :log "=========================================="
call :log "[INFO] GitHub Actions: %GITHUB_ACTIONS_URL%"
call :log "[INFO] Website: %WEBSITE_URL%"

call :log ""
call :log "=========================================="
call :log "  All Done!"
call :log "=========================================="
call :log "[INFO] Log saved: %LOG_FILE%"
call :log ""

REM Only pause and open browser in interactive mode
if "%INTERACTIVE%"=="1" (
    pause
    start "" "%GITHUB_ACTIONS_URL%"
    timeout /t 2 /nobreak >nul
    start "" "%WEBSITE_URL%"
)
