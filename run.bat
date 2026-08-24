@echo off
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Installing/updating dependencies...
call venv\Scripts\pip install -r requirements.txt
echo Starting Seminar Hall Booking Portal...
echo Please open http://127.0.0.1:5000 in your browser.
call venv\Scripts\python app.py
pause
