@echo off
chcp 65001 >nul

cls
echo ==========================================
echo   Echo CMS - Status Check
echo ==========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%..\..\"
cd /d "%PROJECT_DIR%"

REM ==================== 1. Check Latest Crawl ====================
echo [1/4] Checking Latest Crawl Log...
echo.

for /f "delims=" %%i in ('dir /b /o-d logs\crawl_*.log 2^>nul') do (
    set "LATEST_LOG=%%i"
    goto :found_log
)
:found_log

if defined LATEST_LOG (
    echo Latest log: logs\%LATEST_LOG%
    echo.
    echo Last 5 lines:
    powershell -Command "Get-Content logs\%LATEST_LOG% -Tail 5"
    echo.
) else (
    echo [WARNING] No crawl logs found
    echo.
)

REM ==================== 2. Check Local Data ====================
echo ==========================================
echo [2/4] Checking Local Data File...
echo.

if exist "public\data.json" (
    for %%A in ("public\data.json") do (
        echo File: public\data.json
        echo Size: %%~zA bytes
        echo Modified: %%~tA
    )
    echo.
    
    REM Extract last_updated from first game
    powershell -Command "$data = Get-Content 'public\data.json' -Raw | ConvertFrom-Json; if ($data.Count -gt 0) { Write-Host 'Last Updated:' $data[0].last_updated }"
    echo.
) else (
    echo [ERROR] data.json not found!
    echo.
)

REM ==================== 3. Check Git Status ====================
echo ==========================================
echo [3/4] Checking Git Status...
echo.

git log -1 --pretty=format:"Latest Commit: %%h - %%s%%nAuthor: %%an%%nDate: %%ad%%n" --date=format:"%%Y-%%m-%%d %%H:%%M:%%S"
echo.
echo.

echo Remote Status:
git fetch >nul 2>&1
git status -sb
echo.

REM ==================== 4. Check GitHub Pages ====================
echo ==========================================
echo [4/4] Checking GitHub Pages Status...
echo.

echo Fetching GitHub Actions status...
echo.

REM Get latest workflow run status
powershell -Command "$url='https://api.github.com/repos/turbotang2333/echo_cms/actions/runs?per_page=1'; try { $response = Invoke-RestMethod -Uri $url -Headers @{'User-Agent'='PowerShell'}; $run = $response.workflow_runs[0]; Write-Host 'Latest Deployment:'; Write-Host '  Status:' $run.status; Write-Host '  Conclusion:' $run.conclusion; Write-Host '  Created:' $run.created_at; Write-Host '  URL:' $run.html_url } catch { Write-Host '[WARNING] Cannot fetch GitHub Actions status' }"

echo.

REM ==================== Summary ====================
echo ==========================================
echo   Summary
echo ==========================================
echo.

echo Website URL: https://turbotang2333.github.io/echo_cms/
echo GitHub Actions: https://github.com/turbotang2333/echo_cms/actions
echo.

echo Quick Actions:
echo   1. Open website: start https://turbotang2333.github.io/echo_cms/
echo   2. Open GitHub Actions: start https://github.com/turbotang2333/echo_cms/actions
echo   3. View latest log: type logs\%LATEST_LOG%
echo.

set /p action="Open website? (y/n): "
if /i "%action%"=="y" (
    start https://turbotang2333.github.io/echo_cms/
    timeout /t 2 /nobreak >nul
    start https://github.com/turbotang2333/echo_cms/actions
)

echo.
pause

