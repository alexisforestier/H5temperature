#!/bin/bash

python3 -m venv .venv
source ./.venv/bin/activate
echo 'Current python env ~~~>' $(which python3)
python3 -m pip install -r requirements.txt 
python3 -m pip install nuitka
python3 -m nuitka --standalone --linux-icon=./h5temperature/resources/h5temp.png --plugin-enable=pyqt5 run.py
mkdir run.dist/h5temperature
cp -r h5temperature/resources run.dist/h5temperature