python -m venv .venv 
call .\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m nuitka --standalone --follow-imports --enable-console --enable-plugin=pyqt5 h5temperature.py
PAUSE