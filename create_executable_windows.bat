python -m venv .venv 
call .\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pip install nuitka
python -m nuitka --standalone --windows-icon-from-ico=.\h5temperature\h5temp.ico --enable-plugin=pyqt5 run.py
set "source=.\h5temperature\resources"
cd .\run.dist\
mkdir h5temperature
cd h5temperature
xcopy "%source%" . /E /I /Y
PAUSE