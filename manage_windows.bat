@echo off
REM Django Fleet Management System - Windows Batch Script
REM This script helps Windows users manage the Django application easily

title Django Fleet Management System

:MENU
cls
echo ========================================================
echo           Django Fleet Management System
echo ========================================================
echo.
echo Please select an option:
echo.
echo 1. Install Dependencies (First Time Setup)
echo 2. Run Database Migrations
echo 3. Create Superuser Account
echo 4. Start Development Server
echo 5. Collect Static Files
echo 6. Open Django Shell
echo 7. Run Tests
echo 8. Export Data to Excel
echo 9. Exit
echo.
set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto INSTALL
if "%choice%"=="2" goto MIGRATE
if "%choice%"=="3" goto SUPERUSER
if "%choice%"=="4" goto RUNSERVER
if "%choice%"=="5" goto COLLECTSTATIC
if "%choice%"=="6" goto SHELL
if "%choice%"=="7" goto TESTS
if "%choice%"=="8" goto EXPORT
if "%choice%"=="9" goto EXIT

echo Invalid choice. Please try again.
pause
goto MENU

:INSTALL
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies!
    pause
) else (
    echo Dependencies installed successfully!
    echo Running initial migrations...
    python manage.py migrate
    echo.
    echo Setup complete! You can now create a superuser account.
    pause
)
goto MENU

:MIGRATE
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate
if errorlevel 1 (
    echo Error running migrations!
) else (
    echo Migrations completed successfully!
)
pause
goto MENU

:SUPERUSER
echo Creating superuser account...
python manage.py createsuperuser
pause
goto MENU

:RUNSERVER
echo Starting Django development server...
echo.
echo The server will start at: http://127.0.0.1:8000/
echo Admin panel: http://127.0.0.1:8000/admin/
echo.
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver
pause
goto MENU

:COLLECTSTATIC
echo Collecting static files...
python manage.py collectstatic
pause
goto MENU

:SHELL
echo Opening Django shell...
python manage.py shell
pause
goto MENU

:TESTS
echo Running tests...
python manage.py test
pause
goto MENU

:EXPORT
echo This will open the web interface for Excel export
echo Make sure the server is running first!
start http://127.0.0.1:8000/bookkeeping/
pause
goto MENU

:EXIT
echo Thank you for using Django Fleet Management System!
pause
exit