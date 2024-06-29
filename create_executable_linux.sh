#!/bin/bash

source ./.venv/bin/activate
echo 'Current python env ~~~>' $(which python3)
python3 -m nuitka --standalone --plugin-enable=pyqt5 run.py
