@echo off

call conda activate ./venv

streamlit run app/main.py
@REM streamlit run app/main.py ^
@REM   --server.runOnSave=true ^
@REM   --server.fileWatcherType=watchdog

pause