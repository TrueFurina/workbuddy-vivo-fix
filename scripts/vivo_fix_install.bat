@echo off
setlocal
:: Self-elevate to administrator (UAC prompt will appear)
NET FILE 1>NUL 2>NUL
if errorlevel 1 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo [STEP 1] Restart Windows Firewall service to clear deadlock...
net stop mpssvc /y
timeout /t 3 /nobreak >nul
net start mpssvc

echo [STEP 2] Verify firewall service responds now...
netsh advfirewall show allprofiles state

echo [STEP 3] Launch vivo PCSuite installer as administrator...
set "INST=C:\Users\Lenovo\AppData\Local\pcsuite-updater\pending\2.0.exe"
if not exist "%INST%" (
  for /r "C:\Users\Lenovo\AppData\Local\pcsuite-updater" %%f in (2.0.exe) do set "INST=%%f"
)
if not exist "%INST%" (
  echo ERROR: installer 2.0.exe not found under pcsuite-updater. Abort.
  pause
  exit /b
)
start "" "%INST%"
echo Installer launched. Watch whether it passes the SetFirewall step this time.
echo If it STILL hangs, the firewall deadlock is driver-level. Fix: reboot, or
echo temporarily disable the Npcap / VirtualBox network hooks, then run this again.
pause
