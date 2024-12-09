@echo off

call conda activate tf
cd app
streamlit run main.py --server.port 3012

pause
