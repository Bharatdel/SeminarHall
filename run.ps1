if (-not (Test-Path .\venv)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

Write-Host "Installing/updating dependencies..." -ForegroundColor Cyan
.\venv\Scripts\pip install -r requirements.txt

Write-Host "Starting Seminar Hall Booking Portal..." -ForegroundColor Green
Write-Host "Please open http://127.0.0.1:5000 in your browser." -ForegroundColor Yellow
.\venv\Scripts\python app.py
