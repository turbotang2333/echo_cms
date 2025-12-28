@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ==================== Configuration ====================
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%..\..\"
cd /d "%PROJECT_DIR%"
set "PROJECT_DIR=%CD%"

REM ==================== Main Process ====================
cls
echo ==========================================
echo   Development Crawler - Test Script
echo ==========================================
echo.
echo Time: %date% %time:~0,8%
echo Path: %PROJECT_DIR%
echo Branch: dev (development)
echo.
echo This script will:
echo   1. Run crawler
echo   2. Commit ALL changes (code + data)
echo   3. Push to dev branch (NOT main)
echo   4. NO production deployment
echo.
pause

REM ==================== Check Branch ====================
echo ==========================================
echo Checking Git Branch
echo ==========================================
echo.

where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git not found
    pause
    exit /b 1
)

REM Get current branch
for /f "tokens=*" %%i in ('git branch --show-current') do set "CURRENT_BRANCH=%%i"

echo Current branch: %CURRENT_BRANCH%
echo.

REM Warning if not on dev (but continue anyway)
git branch --show-current | findstr /x "dev" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] You are not on dev branch: %CURRENT_BRANCH%
    echo This script is designed for dev branch development.
    echo.
    echo Press Ctrl+C to cancel, or any key to continue anyway...
    pause >nul
    echo.
) else (
    echo [SUCCESS] On dev branch
    echo.
)

REM ==================== Step 1: Run Crawler ====================
echo ==========================================
echo Step 1/3: Running Crawler
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
echo Step 2/3: Checking Changes
echo ==========================================
echo.

git status --short

git diff --quiet
set HAS_CHANGES=%errorlevel%

git diff --cached --quiet
set HAS_STAGED=%errorlevel%

if %HAS_CHANGES% equ 0 if %HAS_STAGED% equ 0 (
    echo.
    echo [WARNING] No changes detected
    echo.
    pause
    exit /b 0
)

echo.
echo [SUCCESS] Changes detected
echo.

REM ==================== Step 3: Commit and Push ====================
echo ==========================================
echo Step 3/3: Commit and Push to Dev Branch
echo ==========================================
echo.

echo Adding all changes...
git add -A

echo.
echo Committing changes...
git commit -m "dev: test update %date:~0,10% %time:~0,5%"

if %errorlevel% neq 0 (
    echo [WARNING] No new commits
    pause
    exit /b 0
)

echo.
echo Pushing to dev branch...
git push origin dev

if %errorlevel% equ 0 (
    echo [SUCCESS] Push completed
) else (
    echo.
    echo [INFO] First push to dev branch, setting upstream...
    git push --set-upstream origin dev
    
    if %errorlevel% equ 0 (
        echo [SUCCESS] Push completed with upstream set
    ) else (
        echo [ERROR] Push failed
        pause
        exit /b 1
    )
)

echo.
echo ==========================================
echo   Development Test Completed!
echo ==========================================
echo.
echo Changes pushed to dev branch
echo Production (main) is NOT affected
echo.
echo Next steps:
echo   1. Test locally: npm run dev
echo   2. Verify data structure works
echo   3. Merge to main when ready:
echo      git checkout main
echo      git merge dev
echo      git push
echo.
pause

