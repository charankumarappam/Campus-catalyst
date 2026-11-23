@echo off
title Package Submission ZIP (Under 24 MB)
cd /d "%~dp0"
echo =====================================================================
echo  Campus Catalyst: Project Packaging Utility
echo  Packaging project for submission (Strictly under 24 MB limit)...
echo =====================================================================
call .venv\Scripts\activate
python package_submission.py
echo.
echo Package created successfully! Press any key to exit.
pause > nul
