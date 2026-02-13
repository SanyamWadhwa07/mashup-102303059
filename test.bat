@echo off
echo ================================
echo Testing Mashup Project 102303059
echo ================================
echo.

echo [1/3] Checking Node.js installation...
node --version
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found! Please install Node.js first.
    pause
    exit /b 1
)
echo OK - Node.js is installed
echo.

echo [2/3] Checking Python packages...
python -c "import flask, yt_dlp, librosa, soundfile, numpy; print('OK - All packages installed')"
if %errorlevel% neq 0 (
    echo ERROR: Some packages are missing!
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)
echo.

echo [3/3] Testing command-line tool...
echo Running: python 102303059.py "Shape of You" 11 21 test_mashup.wav
python 102303059.py "Shape of You" 11 21 test_mashup.wav
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Command-line tool failed!
    echo Check the error messages above.
    pause
    exit /b 1
)
echo.

echo ================================
echo SUCCESS! All tests passed.
echo ================================
echo.
echo To run the web app:
echo    python app.py
echo.
echo Then open: http://127.0.0.1:5000
echo.
pause
