@echo off
python -m venv venv
call venv\Scripts\activate.bat

streamlit run app.py
