@echo off
chcp 936 >nul 2>&1
title WorkBuddy Force Fix v4
setlocal

rem ============ 管理员权限自检 ============
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo   正在请求管理员权限... 请在弹窗中点『是』
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo.
echo ====================================================
echo    WorkBuddy 强制修复安装  v4
echo ====================================================
echo.
echo   [OK] 已获得管理员权限
echo.
echo   本脚本会:
echo     1. 用 TerminateProcess 清掉所有卡死的安装器僵尸进程
echo     2. 强制结束全部 WorkBuddy 进程(绕过 QmProtector 退出流程)
echo     3. 禁用 QmProtector 保护目录(改名, 可自动还原)
echo     4. 以管理员权限启动全新 5.5.3 安装器并置顶窗口
echo     5. 监控 90 秒, 确认是否真的开始写入
echo.
echo   警告: 所有 WorkBuddy 窗口会被关闭(含进行中的对话).
echo.
echo ====================================================
echo.
pause

set "PY1=C:\Users\Lenovo\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "PY2=D:\miniconda3_new\python.exe"
set "SCRIPT=%~dp0wb_kill_install.py"

set "PY="
if exist "%PY1%" set "PY=%PY1%"
if not defined PY if exist "%PY2%" set "PY=%PY2%"
if not defined PY (
  echo [错误] 找不到 Python 解释器.
  echo.
  pause
  exit /b 1
)

echo 解释器: %PY%
echo.
"%PY%" "%SCRIPT%"

echo.
echo 执行完毕. 详细日志见桌面 kill-result.txt
echo.
pause
