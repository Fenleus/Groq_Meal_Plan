@echo off
echo ==============================================
echo Family Nutrition Management System
echo ==============================================
echo.
echo Choose which interface to launch:
echo.
echo 1. Parent Interface (Port 8501)
echo 2. Nutritionist Interface (Port 8502)
echo 3. Both (in separate windows)
echo 4. Admin Interface (Port 8503)
echo 5. All Interfaces (in separate windows)
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Starting Parent Interface...
    streamlit run parent_ui.py --server.port 8501
) else if "%choice%"=="2" (
    echo Starting Nutritionist Interface...  
    streamlit run nutritionist_ui.py --server.port 8502
) else if "%choice%"=="3" (
    echo Starting both interfaces...
    start cmd /k "streamlit run parent_ui.py --server.port 8501"
    start cmd /k "streamlit run nutritionist_ui.py --server.port 8502"
) else if "%choice%"=="4" (
    echo Starting Admin Interface...
    streamlit run admin_ui.py --server.port 8503
) else if "%choice%"=="5" (
    echo Starting all interfaces...
    start cmd /k "streamlit run parent_ui.py --server.port 8501"
    start cmd /k "streamlit run nutritionist_ui.py --server.port 8502"
    start cmd /k "streamlit run admin_ui.py --server.port 8503"
) else (
    echo Invalid choice. Please run the script again.
)

pause
