@echo off
title Campus Catalyst - College Event Registration Manager (Streamlit UI)
cd /d "%~dp0"
echo =====================================================================
echo  Campus Catalyst: College Event Registration Manager (Project #8)
echo  Domain: Education & Student Life
echo  Launching Streamlit Web Application on http://localhost:8501...
echo =====================================================================
call .venv\Scripts\activate
streamlit run app_streamlit.py --server.port 8501 --server.headless false
pause
