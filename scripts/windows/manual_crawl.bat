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

REM ==================== Main Process ====================
cls
echo ==========================================
echo   Crawler System - Manual Update
echo ==========================================
echo.
echo Time: %date% %time:~0,8%
echo Path: %PROJECT_DIR%
echo.

REM ==================== Step 1: Run Crawler ====================
echo ==========================================
echo Step 1/4: Running Crawler
echo ==========================================
echo.

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
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo Running crawler...
echo.

%PYTHON_CMD% -u "%PROJECT_DIR%\crawler\main.py"

if %errorlevel% neq 0 (
    echo.
    echo [FAILED] Crawler execution failed
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Crawler completed
echo.

REM ==================== Step 2: Check Changes ====================
echo ==========================================
echo Step 2/4: Checking Changes
echo ==========================================
echo.

where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git not found
    pause
    exit /b 1
)

git diff --quiet public/data.json archive/
if %errorlevel% equ 0 (
    echo [WARNING] No data changes detected
    echo.
    pause
    exit /b 0
)

echo [SUCCESS] Data changes detected
echo.

REM ==================== Step 3: Commit and Push ====================
echo ==========================================
echo Step 3/4: Commit and Push to GitHub
echo ==========================================
echo.

git stash -u >nul 2>&1
set STASH_CREATED=%errorlevel%

git add public/data.json archive/
git commit -m "data: manual update %date:~0,10% %time:~0,5%"

if %errorlevel% neq 0 (
    echo [WARNING] No new commits
    if %STASH_CREATED% equ 0 (
        git stash pop >nul 2>&1
    )
    pause
    exit /b 0
)

git pull --rebase
if %errorlevel% neq 0 (
    git checkout --ours public/data.json 2>nul
    git checkout --ours archive/ 2>nul
    git add public/data.json archive/
    echo | git rebase --continue
)

git push

if %errorlevel% equ 0 (
    echo [SUCCESS] Push completed
) else (
    echo [ERROR] Push failed
    pause
    exit /b 1
)

if %STASH_CREATED% equ 0 (
    git stash pop >nul 2>&1
)

echo.

REM ==================== Step 4: Open Pages ====================
echo ==========================================
echo Step 4/4: View Deployment
echo ==========================================
echo.

start "" "%GITHUB_ACTIONS_URL%"
timeout /t 2 /nobreak >nul

echo.
echo ==========================================
echo   Completed!
echo ==========================================
echo.
pause
start "" "%WEBSITE_URL%"

