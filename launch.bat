@echo off
REM Launch all three interfaces (Parent, Nutritionist, Admin) in minimized command prompt windows

start "" /min cmd /c "streamlit run parent_ui.py --server.port 8501"
start "" /min cmd /c "streamlit run nutritionist_ui.py --server.port 8502"
start "" /min cmd /c "streamlit run admin_ui.py --server.port 8503"

exit
