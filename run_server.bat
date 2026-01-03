@echo off
REM Script to run the secure email system web server on Windows

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the Flask server
python app.py

pause

