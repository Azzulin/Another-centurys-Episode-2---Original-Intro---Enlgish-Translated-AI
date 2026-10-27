@echo off
rem Opens PCSX2 with the test ISO (unless it is already running) and starts crash_watch.py. Double-click to run.
set ISO=ACE2-EN-0.0.17.iso
set PCSX2=%USERPROFILE%\Downloads\PCSX2\pcsx2-qt.exe
cd /d "%~dp0..\.."
tasklist /fi "imagename eq pcsx2-qt.exe" | find /i "pcsx2-qt.exe" >nul || start "" "%PCSX2%" -- "%CD%\work\output\%ISO%"
py -3.12 tools\research\crash_watch.py watch --iso "work\output\%ISO%"
pause