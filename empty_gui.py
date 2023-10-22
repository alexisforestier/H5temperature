import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (QApplication, 
							 QWidget,
							 QLabel,
							 QSpinBox,
							 QGroupBox,
							 QPushButton,
							 QListWidget,
							 QFormLayout,
							 QVBoxLayout,
							 QHBoxLayout)



class MainWindow(QWidget):
	def __init__(self):
		super().__init__()

		self.resize(1100,800)
		
		# left layout	
		load_button = QPushButton('Load h5')
		clear_button = QPushButton('Clear')

		currentfile_layout = QHBoxLayout()
		currentfile_label = QLabel('Current file:')
		currentfilename_label = QLabel('name')
		currentfile_layout.addWidget(currentfile_label)
		currentfile_layout.addWidget(currentfilename_label)

		files_list = QListWidget()
		files_list.addItem('Hello')
		files_list.addItem('I am')
		files_list.addItem('doing')
		files_list.addItem('a test')

		leftlayout = QVBoxLayout()
		leftlayout.addWidget(load_button)
		leftlayout.addLayout(currentfile_layout)
		leftlayout.addWidget(files_list)
		leftlayout.addWidget(clear_button)

		left_groupbox = QGroupBox('Data')
		left_groupbox.setLayout(leftlayout)

		left_groupbox.setMinimumWidth(200)


		# right layout
		lowerbound_spinbox = QSpinBox()
		upperbound_spinbox = QSpinBox()
		delta_spinbox = QSpinBox()

		fit_button = QPushButton('Fit')
		results_button = QPushButton('Results')

		fitparam_form = QFormLayout()
		fitparam_form.addRow('Lower limit (nm):', lowerbound_spinbox)
		fitparam_form.addRow('Upper limit (nm):', upperbound_spinbox)
		fitparam_form.addRow('2-color delta (px):', delta_spinbox)
		
		fit_layout = QVBoxLayout()
		fit_layout.addLayout(fitparam_form)
		fit_layout.addWidget(fit_button)
		fit_layout.addWidget(results_button)
		fit_layout.addStretch()

		right_groupbox = QGroupBox('Fit parameters')
		right_groupbox.setLayout(fit_layout)
		right_groupbox.setMinimumWidth(200)


		# center layout
		center_groupbox = QGroupBox('Plots')


		layout = QHBoxLayout()
		layout.addWidget(left_groupbox, stretch=1)
		layout.addStretch()
		layout.addWidget(center_groupbox, stretch=10)
		layout.addStretch()
		layout.addWidget(right_groupbox, stretch=1)
		
		self.setLayout(layout)



app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()