python -m venv .venv
call .\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pip install nuitka
python -m nuitka --standalone --windows-icon-from-ico=.\h5temperature\resources\h5temp.ico --enable-plugin=pyqt5 run.py
@echo off 
echo COPY RESOURCES
set "source=.\h5temperature\resources"
set "dest=.\run.dist\h5temperature\resources"
echo source  %source%
echo dest  %dest%
xcopy "%source%" "%dest%" /E /I /Y
ren .\run.dist\run.exe h5temperature.exe
rename ".\run.dist" "h5temperature"
PAUSE