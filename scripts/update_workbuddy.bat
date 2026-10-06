@echo off
setlocal
:: Self-elevate to administrator (UAC prompt will appear)
NET FILE 1>NUL 2>NUL
if errorlevel 1 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
:: Prefer the copy on the Desktop next to this bat; fall back to the TEMP cache
set "INST=%~dp0WorkBuddy-Setup-5.5.6.38337834.exe"
if not exist "%INST%" (
  set "INST=C:\Users\Lenovo\AppData\Local\Temp\workbuddy-update-x64\WorkBuddy-Setup-5.5.6.38337834.exe"
)
if not exist "%INST%" (
  echo ERROR: installer not found on Desktop or in TEMP. Abort.
  pause
  exit /b
)
echo Launching WorkBuddy 5.5.6 installer in update mode...
echo IMPORTANT: make sure ALL WorkBuddy windows/tray icons are closed first.
start "" "%INST%" /UPDATE=1 /D=D:\WorkBuddy
echo If a UAC prompt appears, click Yes. After it finishes, reopen WorkBuddy.
pause
