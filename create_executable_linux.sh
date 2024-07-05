#!/bin/bash

python3 -m venv .venv
source ./.venv/bin/activate
echo 'Current python env ~~~>' $(which python3)
python3 -m pip install -r requirements.txt 
python3 -m pip install nuitka
python3 -m nuitka --standalone --plugin-enable=pyqt5 run.py
