@echo off

call conda activate ./venv

streamlit run app/main.py

pause