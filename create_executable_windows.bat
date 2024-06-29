python -m venv .venv 
call .\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pip install nuitka
python -m nuitka --standalone --enable-plugin=pyqt5 run.py
PAUSE