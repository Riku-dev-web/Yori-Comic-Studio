@echo off
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 (echo Python 3 est requis. & pause & exit /b 1)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (echo Installation impossible. & pause & exit /b 1)
python -m PyInstaller --noconfirm --clean --onefile --windowed --name YoriComicStudio main.py
if errorlevel 1 (echo Compilation impossible. & pause & exit /b 1)
echo.
echo EXE CREE : dist\YoriComicStudio.exe
pause
