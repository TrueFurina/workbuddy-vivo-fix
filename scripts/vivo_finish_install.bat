@echo off
NET SESSION >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
start "" "C:\Users\Lenovo\AppData\Local\pcsuite-updater\pending\2.0.exe"
