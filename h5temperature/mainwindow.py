#   Copyright (C) 2023-2024 Alexis Forestier (alforestier@gmail.com)
#   
#   This file is part of h5temperature.
#   
#   h5temperature is free software: you can redistribute it and/or modify it 
#   under the terms of the GNU General Public License as published by the 
#   Free Software Foundation, either version 3 of the License, or 
#   (at your option) any later version.
#   
#   h5temperature is distributed in the hope that it will be useful, 
#   but WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
#   See the GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License 
#   along with h5temperature. If not, see <https://www.gnu.org/licenses/>.

import numpy as np
import h5py
from PyQt5.QtWidgets import (QApplication, 
                             QWidget,
                             QLabel,
                             QSpinBox,
                             QCheckBox,
                             QTableWidget,
                             QTableWidgetItem,
                             QAbstractItemView,
                             QHeaderView,
                             QGroupBox,
                             QPushButton,
                             QTreeWidget,
                             QTreeWidgetItem,
                             QFormLayout,
                             QVBoxLayout,
                             QHBoxLayout,
                             QFileDialog,
                             QMessageBox,
                             QSizePolicy)

from h5temperature import __version__
import h5temperature.physics as Ph 
from h5temperature.formats import get_data_from_h5group, get_data_from_ascii
from h5temperature.models import BlackBodySpec
from h5temperature.views import (FourPlotsCanvas,
                                 ChooseDeltaWindow)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('h5temperature {}'.format(__version__))
        self.resize(1400,800)

        # data stored in MainWindow
        self.filepath = str()
        self.data = dict()

        # current parameters in the mainwindow and their default values
        self.pars = dict(lowerb = 550,
                         upperb = 900,
                         delta = 100)

        # left layout   
        load_button = QPushButton('Load h5')
        reload_button = QPushButton('Reload')
        loadascii_button = QPushButton('Load ASCII')
        clear_button = QPushButton('Clear')
        exportraw_button = QPushButton('Export current')

        topleftbuttonslayout = QHBoxLayout()
        topleftbuttonslayout.addWidget(load_button)
        topleftbuttonslayout.addWidget(reload_button)
        topleftbuttonslayout.addWidget(loadascii_button)
        

        currentfile_layout = QHBoxLayout()
        currentfile_label = QLabel('Current file:')
        self.currentfilename_label = QLabel('')
        self.currentfilename_label.setStyleSheet("border: 1px solid black;\
                                                  background-color: white")

        currentfile_layout.addWidget(currentfile_label, stretch=0)
        currentfile_layout.addWidget(self.currentfilename_label, stretch=10)

        self.dataset_tree = QTreeWidget()
        self.dataset_tree.setColumnCount(1)
        self.dataset_tree.setSelectionMode(1) # single selection
        self.dataset_tree.setHeaderHidden(True)

        leftlayout = QVBoxLayout()
        leftlayout.addLayout(topleftbuttonslayout)
        leftlayout.addLayout(currentfile_layout)
        leftlayout.addWidget(self.dataset_tree)
        leftlayout.addWidget(clear_button)
        leftlayout.addWidget(exportraw_button)

        left_groupbox = QGroupBox('Data')
        left_groupbox.setLayout(leftlayout)

        left_groupbox.setMinimumWidth(250)

        # right layout
        lowerbound_spinbox = QSpinBox()
        upperbound_spinbox = QSpinBox()
        self.delta_spinbox = QSpinBox()

        lowerbound_spinbox.setMinimum(1)
        upperbound_spinbox.setMinimum(1)
        self.delta_spinbox.setMinimum(1)
        lowerbound_spinbox.setMaximum(9999)
        upperbound_spinbox.setMaximum(9999)
        self.delta_spinbox.setMaximum(9999)
        
        # set default values in Widgets:
        lowerbound_spinbox.setValue(self.pars.get('lowerb'))
        upperbound_spinbox.setValue(self.pars.get('upperb'))
        self.delta_spinbox.setValue(self.pars.get('delta'))

        choosedelta_button = QPushButton('Choose delta')
        fit_button = QPushButton('Fit')

        fitparam_form = QFormLayout()
        fitparam_form.addRow('Lower limit (nm):', lowerbound_spinbox)
        fitparam_form.addRow('Upper limit (nm):', upperbound_spinbox)
        fitparam_form.addRow('2-color delta (px):', self.delta_spinbox)
        

        self.results_table = QTableWidget(6,1)
        self.results_table.setStyleSheet('QTableWidget '
                                         '{border: 1px solid gray ;'
                                          'font-weight: bold ;'
                                          'background-color: white ;}')

        self.results_table.resizeRowsToContents()
        self.results_table.resizeColumnsToContents()
        self.results_table.horizontalHeader().setVisible(False)
        self.results_table.horizontalHeader().setSectionResizeMode( 
                    QHeaderView.Stretch)
        self.results_table.verticalHeader().setSectionResizeMode( 
                    QHeaderView.Stretch)
        self.results_table.setSizePolicy(QSizePolicy.Preferred, 
                                QSizePolicy.Preferred)
        # not selectable, not editable:
        self.results_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setVerticalHeaderLabels(["T Planck (K)", 
                                                    "T Wien (K)",
                                                    "T 2-color (K)",
                                                    "T 2-c std dev (K)",
                                                    "multiplier Planck",
                                                    "multiplier Wien"])

        fit_layout = QVBoxLayout()
        fit_layout.addLayout(fitparam_form)
        fit_layout.addWidget(choosedelta_button)
        fit_layout.addWidget(fit_button)
        fit_layout.addWidget(self.results_table)
        fit_layout.addStretch()

        right_groupbox = QGroupBox('Fitting')
        right_groupbox.setLayout(fit_layout)
        right_groupbox.setMinimumWidth(250)

        # center layout
        center_groupbox = QGroupBox()
        center_groupbox.setStyleSheet('QGroupBox  {border: 2px solid gray;\
                                                  background-color: white;}')
        plot_layout = QVBoxLayout()

        # set empty plots
        self.canvas = FourPlotsCanvas(self)
        self.toolbar = self.canvas.get_NavigationToolbar(self)
        self.toolbar.setStyleSheet("font-size: 18px;")
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)

        center_groupbox.setLayout(plot_layout)

        # setup choosedelta window
        self.choosedelta_win = ChooseDeltaWindow()
        self.choosedelta_win.setStyleSheet("background-color: white")

        # about button
        about_button = QPushButton('About')
        right_groupbox_about = QVBoxLayout()
        right_groupbox_about.addWidget(right_groupbox)
        right_groupbox_about.addWidget(about_button)

        layout = QHBoxLayout()
        layout.addWidget(left_groupbox, stretch=3)
        layout.addStretch()
        layout.addWidget(center_groupbox, stretch=12)
        layout.addStretch()
        layout.addLayout(right_groupbox_about, stretch=3)
        
        self.setLayout(layout)

        # connects :
        about_button.clicked.connect(self.show_about)
        load_button.clicked.connect(self.load_h5file)
        loadascii_button.clicked.connect(self.load_ascii)
        reload_button.clicked.connect(self.reload_h5file)
        clear_button.clicked.connect(self.clear_all)

        exportraw_button.clicked.connect(
            lambda: self.export_current_raw(self.dataset_tree.currentItem()))

        choosedelta_button.clicked.connect(
            lambda: self.choose_delta(self.dataset_tree.currentItem()))

#        self.dataset_tree.currentItemChanged.connect(
#            lambda: self.update(self.dataset_tree.currentItem().text(0)))
        self.dataset_tree.currentItemChanged.connect(self.update)

        fit_button.clicked.connect(
            lambda: self.update(self.dataset_tree.currentItem()))

        # on change in parameters widgets it is updated in self.pars
        lowerbound_spinbox.valueChanged.connect(
                lambda x: self.pars.__setitem__('lowerb', x))
        upperbound_spinbox.valueChanged.connect(
                lambda x: self.pars.__setitem__('upperb', x))
        self.delta_spinbox.valueChanged.connect(
                lambda x: self.pars.__setitem__('delta', x))

        lowerbound_spinbox.editingFinished.connect(
            lambda: self.update(self.dataset_tree.currentItem()))
        upperbound_spinbox.editingFinished.connect(
            lambda: self.update(self.dataset_tree.currentItem()))
        self.delta_spinbox.editingFinished.connect(
            lambda: self.update(self.dataset_tree.currentItem()))

    def get_data_from_tree_item(self, item):
        if item:
            key = item.text(0)
            # if it is a sub item:
            if item.parent() is not None:
                parent_key = item.parent().text(0)
                return self.data[parent_key][key]
            # if it is a proper individual measurementy:
            elif item.childCount() == 0:
                return self.data[key]
            # it may be the main key of a serie of measurements:
            else: 
                return None 

    def get_h5file_content(self):
        # read h5 file and store in self.data: 
        with h5py.File(self.filepath, 'r') as file:
            for nam, group in file.items():
                if group is not None: 
                # get temperature measurements only
                    if 'measurement/T_planck' in group:
                    # not already loaded only / no identical key!
                        if nam not in self.data:
                        # populate data:
                            d = get_data_from_h5group(group)
                            if type(d) is dict:
                                self.data[nam] = BlackBodySpec(nam, **d)
                            elif type(d) is list:
                                # if multiple measurements, element is a dict:
                                self.data[nam] = dict()
                                for i, di in enumerate(d):
                                    k = '{}'.format(i)
                                    self.data[nam][k] = BlackBodySpec(nam,**di)


    def populate_dataset_tree(self):        
        if self.data:
            # sort datasets in chronological order
            # this may one day be a class method?
            def get_timestamp(k, elem):
                if isinstance(elem, dict):
                    return self.data[k]['0'].timestamp
                else:
                    return self.data[k].timestamp

            try:
                names_chrono = sorted(self.data.keys(), 
                          key = lambda k:  get_timestamp(k, self.data[k]))
            except:
                QMessageBox.warning(self, 'Warning',
                'Problem with measurement dates and times.\n'
                'Chronological order will NOT be used.')     

                names_chrono = self.data.keys()
            
            prev_items = [self.dataset_tree.topLevelItem(x).text(0) 
                    for x in range(self.dataset_tree.topLevelItemCount())]
            # new items will always be added at the end
            # thus data are in chronological order within 
            # a given h5 loaded but not globally. 
            for n in names_chrono:
                if n not in prev_items:
                    item_n = QTreeWidgetItem(self.dataset_tree, [n])
                    if type(self.data[n]) is dict:
                        for k in self.data[n].keys():
                            item_k = QTreeWidgetItem(item_n, [str(k)])
                    #test = QTreeWidgetItem(item_n, ["test1","test2"])
                    #self.dataset_tree.addTopLevelItem(QTreeWidgetItem([n]))


    def show_about(self):
        text = '<center>' \
               '<h1> h5temperature </h1>' \
               '<h2> version {}</h2>'.format(__version__) + '<br>' \
               'Analysis methods used in h5temperature are detailed in: ' \
               '<a href=\"https://doi.org/10.1080/08957950412331331718\">' \
               'Benedetti and Loubeyre (2004), ' \
               'High Pressure Research, 24:4, 423-445</a> <br><br>' \
               'Copyright 2023-2024 Alexis Forestier ' \
               '(alforestier@gmail.com) <br><br>' \
               '<small> <small> <small>' \
               'h5temperature is free software: you can redistribute ' \
               'it and/or modify it under the terms of the '  \
               'GNU General Public License as published by the ' \
               'Free Software Foundation, either version 3 of the '  \
               'License, or (at your option) any later version. ' \
               'h5temperature is distributed in the hope that it '  \
               'will be useful, but WITHOUT ANY WARRANTY; without '  \
               'even the implied warranty of MERCHANTABILITY or ' \
               'FITNESS FOR A PARTICULAR PURPOSE. See the GNU ' \
               'General Public License for more details. ' \
               'You should have received a copy of the GNU General ' \
               'Public License along with h5temperature. '  \
               'If not, see <a href=\"https://www.gnu.org/licenses/\">' \
               'https://www.gnu.org/licenses/</a>.' \
               '</small> </small> </small>' \
               '</center>' 
        msg = QMessageBox(self)
        msg.setWindowTitle("About h5temperature")
        msg.setText(text)
        msg.setStyleSheet("background-color: white;")
        msg.exec_()


    def load_h5file(self):
        options = QFileDialog.Options()
        # ! use Native dialog or qt dialog... 
        # ! Must be checked on different platforms !

    #   options |= QFileDialog.DontUseNativeDialog
        self.filepath, _ = QFileDialog.getOpenFileName(self,
            "Load HDF5 file", "","HDF5 file *.h5 *.hdf5 (*.h5 *.hdf5)", 
            options=options)

        if self.filepath:
            self.get_h5file_content()
            self.populate_dataset_tree()
            self.currentfilename_label.setText(self.filepath.split('/')[-1])

    def reload_h5file(self):
        if self.filepath:
            self.get_h5file_content()
            self.populate_dataset_tree()

    def load_ascii(self):
        options = QFileDialog.Options()
        # ! use Native dialog or qt dialog... 
        # ! Must be checked on different platforms !

    #   options |= QFileDialog.DontUseNativeDialog
        self.filepath, _ = QFileDialog.getOpenFileName(self,
            "Load Text file", "","Text File *.txt *.dat *.asc "
                        "(*.txt *.dat *.asc);;Any File *.* (*.*)", 
            options=options)

        if self.filepath:
            d = get_data_from_ascii(self.filepath)

            name = self.filepath.split('/')[-1]
            # populate
            self.data[name] = BlackBodySpec(name, **d)
            self.populate_dataset_tree()

            
    def export_current_raw(self, item):
        options =  QFileDialog.Options() 
        #options = QFileDialog.DontUseNativeDialog
        # ! Must be checked on different platforms !
        filename, filetype = \
            QFileDialog.getSaveFileName(self,
                                        "h5temperature: Export to ASCII", 
                                        "",
                                        "Text File (*.txt);;All Files (*)", 
                                        options=options)

        if filename:
            if filetype == 'Text File (*.txt)':
                if '.txt' in filename:
                    pass
                else:
                    filename += '.txt'
    
            current = self.get_data_from_tree_item(item)

            # create empty array of len(lam) to be saved in txt
            twocolor_ = np.empty( len(current.lam) )
            # fill with NaN
            twocolor_.fill(np.nan) 

            nans = np.empty(current.pars['delta'])
            nans.fill(np.nan)

            dat1 = np.concatenate([current.twocolor, nans])
            # populate twocolor_ only where data should be, the rest is nan
            twocolor_[current.ind_interval] = dat1

            data_ = np.column_stack((current.lam,
                                     current.planck,
                                     current.wien,
                                     twocolor_))
            np.savetxt(filename, 
                       data_, 
                       delimiter='\t', 
                       comments='',
                       header='lambda\tPlanck\tWien\ttwocolor')


    def choose_delta(self, item):

        current = self.get_data_from_tree_item(item)

        # clear previous :
        self.choosedelta_win.canvas.ax.clear()

        alldeltas = np.array(range(300))
        allstddevs = np.array( [np.std(Ph.temp2color(
                                current.lam[current.ind_interval], 
                                current.wien[current.ind_interval], 
                                di)) for di in alldeltas ] )

        self.choosedelta_win.canvas.ax.scatter(alldeltas, 
                                               allstddevs,
                                               marker='X',
                                               edgecolor='k',
                                               color='royalblue',
                                               alpha=0.5,
                                               s=30)

        vline = self.choosedelta_win.canvas.ax.axvline(current.pars['delta'],
                                               color='k',
                                               linestyle='dashed',
                                               linewidth=1)

        self.choosedelta_win.canvas.ax.set_ylim([0,3e3])

        self.choosedelta_win.canvas.draw()
        self.choosedelta_win.show()

        def get_xclick(event):
            x = int(event.xdata)
            self.delta_spinbox.setValue(x)
            vline.set_xdata([x])
            self.choosedelta_win.canvas.draw()
            
            # necessary as editingFinished does not send signal here
            self.update(item)
            
        # click event
        self.choosedelta_win.canvas.mpl_connect('button_press_event', 
                            get_xclick)


    def clear_all(self):
        self.filepath = str()
        self.currentfilename_label.setText('')
        self.data = dict()
        self.dataset_tree.clear()
        self.results_table.clearContents()

        self.canvas.clear_all()

    def eval_fits(self, item):
        # eval all quantities for a given spectrum
        current = self.get_data_from_tree_item(item)
        try:
            # start with wien to get a reasonable initial value for planck:
            current.eval_wien_fit()
            current.eval_planck_fit()            
            # eval two color at the end in all cases
            current.eval_twocolor()

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def update(self, item):
            current = self.get_data_from_tree_item(item)

            if current:
                # if parameters have changed then we fit again
                # if current was never fitted current.pars is None 
                if not current.pars == self.pars:
                    current.set_pars(self.pars)
                    self.eval_fits(item)
                
                self.canvas.update_all(current)
                self.update_table(item)

            else:
                # empty if no data e.g. main item of a serie
                self.canvas.clear_all()
                self.results_table.clearContents()

    def update_table(self, item):

        current = self.get_data_from_tree_item(item)

        self.results_table.setItem(0, 0, 
                    QTableWidgetItem(str(round(current.T_planck))))
        self.results_table.setItem(0, 1, 
                    QTableWidgetItem(str(round(current.T_wien))))
        self.results_table.setItem(0, 2, 
                    QTableWidgetItem(str(round(current.T_twocolor))))
        self.results_table.setItem(0, 3, 
                    QTableWidgetItem(str(round(current.T_std_twocolor))))
        self.results_table.setItem(0, 4, 
                    QTableWidgetItem(str(round(current.eps_planck,3))))
        self.results_table.setItem(0, 5, 
                    QTableWidgetItem(str(round(current.eps_wien,3))))