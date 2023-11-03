import sys
import numpy as np
import pandas as pd
import h5py
from PyQt5.QtWidgets import (QApplication, 
							 QWidget,
							 QLabel,
							 QSpinBox,
							 QCheckBox,
#							 QDoubleSpinBox,
							 QGroupBox,
							 QPushButton,
							 QListWidget,
							 QFormLayout,
							 QVBoxLayout,
							 QHBoxLayout,
							 QFileDialog)



class MainWindow(QWidget):
	def __init__(self):
		super().__init__()

		self.resize(1100,800)
		
		self.data = dict()
		self.filepath = str()

		# left layout	
		load_button = QPushButton('Load h5')
		reload_button = QPushButton('Reload')
		clear_button = QPushButton('Clear')

		topleftbuttonslayout = QHBoxLayout()
		topleftbuttonslayout.addWidget(load_button)
		topleftbuttonslayout.addWidget(reload_button)

		currentfile_layout = QHBoxLayout()
		currentfile_label = QLabel('Current file:')
		self.currentfilename_label = QLabel('')

		currentfile_layout.addWidget(currentfile_label)
		currentfile_layout.addWidget(self.currentfilename_label)

		self.dataset_list = QListWidget()


		leftlayout = QVBoxLayout()
		leftlayout.addLayout(topleftbuttonslayout)
		leftlayout.addLayout(currentfile_layout)
		leftlayout.addWidget(self.dataset_list)
		leftlayout.addWidget(clear_button)

		left_groupbox = QGroupBox('Data')
		left_groupbox.setLayout(leftlayout)

		left_groupbox.setMinimumWidth(230)

		# right layout
		lowerbound_spinbox = QSpinBox()
		upperbound_spinbox = QSpinBox()
		delta_spinbox = QSpinBox()

		lowerbound_spinbox.setMinimum(400)
		upperbound_spinbox.setMinimum(400)
		delta_spinbox.setMinimum(1)
		lowerbound_spinbox.setMaximum(1200)
		upperbound_spinbox.setMaximum(1200)
		delta_spinbox.setMaximum(1000)
		# default values:
		lowerbound_spinbox.setValue(400)
		upperbound_spinbox.setValue(800)
		delta_spinbox.setValue(100)

		bg_checkbox = QCheckBox('Fit background')

		fit_button = QPushButton('Fit')
		results_button = QPushButton('Results')

		fitparam_form = QFormLayout()
		fitparam_form.addRow('Lower limit (nm):', lowerbound_spinbox)
		fitparam_form.addRow('Upper limit (nm):', upperbound_spinbox)
		fitparam_form.addRow('2-color delta (px):', delta_spinbox)
		

		fit_layout = QVBoxLayout()
		fit_layout.addLayout(fitparam_form)
		fit_layout.addWidget(bg_checkbox)
		fit_layout.addWidget(fit_button)
		fit_layout.addWidget(results_button)
		fit_layout.addStretch()

		right_groupbox = QGroupBox('Fit parameters')
		right_groupbox.setLayout(fit_layout)
		right_groupbox.setMinimumWidth(200)


		# center layout
		center_groupbox = QGroupBox('Plots')


		layout = QHBoxLayout()
		layout.addWidget(left_groupbox, stretch=2)
		layout.addStretch()
		layout.addWidget(center_groupbox, stretch=10)
		layout.addStretch()
		layout.addWidget(right_groupbox, stretch=1)
		
		self.setLayout(layout)


		load_button.clicked.connect(self.load_h5file)
		clear_button.clicked.connect(self.clear)

	def load_h5file(self):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		self.filepath, _ = QFileDialog.getOpenFileName(self,
			"Load HDF5 file", "","HDF5 file (*.h5)", 
			options=options)
		if self.filepath != str():
			file = h5py.File(self.filepath, 'r')
			for nam, dat in file.items():
				# get temperature measurements only
				if 'measurement/T_planck' in dat:
					self.data[nam] = dat['measurement']

			self.currentfilename_label.setText(self.filepath.split('/')[-1])
			self.dataset_list.addItems(self.data.keys())

	def clear(self):
		if self.filepath != str():
			self.filepath = str()
			self.currentfilename_label.setText('')
			self.data = dict()
			self.dataset_list.clear()


app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()