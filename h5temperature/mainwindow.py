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
                             QMenu,
                             QAction,
                             QGroupBox,
                             QPushButton,
                             QTreeWidget,
                             QTreeWidgetItem,
                             QFormLayout,
                             QVBoxLayout,
                             QHBoxLayout,
                             QFileDialog,
                             QMessageBox)

from PyQt5.QtCore import Qt, pyqtSlot, QPoint

from h5temperature import __version__
import h5temperature.physics as Ph 
from h5temperature.formats import get_data_from_h5group, get_data_from_ascii
from h5temperature.models import BlackBodySpec, TemperaturesBatch
from h5temperature.plots import (FourPlotsCanvas,
                                 ChooseDeltaWindow,
                                 BatchWindow)
from h5temperature.tables import SingleFitResultsTable


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f'h5temperature {__version__}')
        self.resize(1600,900)

        # data stored in MainWindow
        self.filepath = str()
        self.data = dict()
#        self.current_batch = None

        # current parameters in the mainwindow and their default values
        self.pars = dict(lowerb = 550,
                         upperb = 900,
                         delta = 100,
                         usebg = False)

        # left layout   
        self.load_button = QPushButton('Load h5')
        self.reload_button = QPushButton('Reload')
        self.clear_button = QPushButton('Clear')
        self.exportraw_button = QPushButton('Export current')

        self.load_menu = QMenu(self)
        self.load_menu.addAction(QAction("Load h5", self))
        self.load_menu.addAction(QAction("Load ASCII", self))

        topleftbuttonslayout = QHBoxLayout()
        topleftbuttonslayout.addWidget(self.load_button)
        topleftbuttonslayout.addWidget(self.reload_button)
        
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
        leftlayout.addWidget(self.clear_button)
        leftlayout.addWidget(self.exportraw_button)

        left_groupbox = QGroupBox('Data')
        left_groupbox.setLayout(leftlayout)

        left_groupbox.setMinimumWidth(250)

        # right layout
        self.lowerbound_spinbox = QSpinBox()
        self.upperbound_spinbox = QSpinBox()
        self.delta_spinbox = QSpinBox()
        self.usebg_checkbox = QCheckBox('Use background')

        self.lowerbound_spinbox.setMinimum(1)
        self.upperbound_spinbox.setMinimum(1)
        self.delta_spinbox.setMinimum(1)
        self.lowerbound_spinbox.setMaximum(9999)
        self.upperbound_spinbox.setMaximum(9999)
        self.delta_spinbox.setMaximum(9999)
        
        # set default values in Widgets:
        self.lowerbound_spinbox.setValue(self.pars.get('lowerb'))
        self.upperbound_spinbox.setValue(self.pars.get('upperb'))
        self.delta_spinbox.setValue(self.pars.get('delta'))
        self.usebg_checkbox.setChecked(self.pars.get('usebg'))

        self.choosedelta_button = QPushButton('Choose delta')
        self.fit_button = QPushButton('Fit')
        self.batch_button = QPushButton('Batch')

        fitparam_form = QFormLayout()
        fitparam_form.addRow('Lower limit (nm):', self.lowerbound_spinbox)
        fitparam_form.addRow('Upper limit (nm):', self.upperbound_spinbox)
        fitparam_form.addRow('2-color delta (px):', self.delta_spinbox)
        
        self.results_table = SingleFitResultsTable()

        fit_layout = QVBoxLayout()
        fit_layout.addLayout(fitparam_form)
        fit_layout.addWidget(self.usebg_checkbox)
        fit_layout.addWidget(self.choosedelta_button)
        fit_layout.addWidget(self.fit_button)
        fit_layout.addWidget(self.batch_button)
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

        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)

        center_groupbox.setLayout(plot_layout)

        # setup choosedelta window
        self.choosedelta_win = ChooseDeltaWindow()
        # setup batch window
        self.batch_win = BatchWindow()

        # about button
        self.about_button = QPushButton('About')
        right_groupbox_about = QVBoxLayout()
        right_groupbox_about.addWidget(right_groupbox)
        right_groupbox_about.addWidget(self.about_button)

        layout = QHBoxLayout()
        layout.addWidget(left_groupbox, stretch=3)
        layout.addStretch()
        layout.addWidget(center_groupbox, stretch=12)
        layout.addStretch()
        layout.addLayout(right_groupbox_about, stretch=3)
        
        self.setLayout(layout)

        self.create_connects()

    def create_connects(self):

        self.about_button.clicked.connect(self.show_about)
        self.load_button.clicked.connect(self.load_h5file)
        self.reload_button.clicked.connect(self.reload_h5file)
        self.clear_button.clicked.connect(self.clear_all)

        self.dataset_tree.currentItemChanged.connect(self.update)
        self.fit_button.clicked.connect(self.update)

        self.batch_button.clicked.connect(self.batch_fit)

        self.load_button.setContextMenuPolicy(Qt.CustomContextMenu)       
        self.load_button.customContextMenuRequested.connect(self.show_load_menu)

        self.exportraw_button.clicked.connect(self.export_current_raw)

        self.choosedelta_button.clicked.connect(self.choose_delta)
        self.choosedelta_win.delta_changed.connect(self.update_delta)

        # on change in parameters widgets it is updated in self.pars
        self.lowerbound_spinbox.valueChanged.connect(
                lambda x: self.pars.__setitem__('lowerb', x))
        self.upperbound_spinbox.valueChanged.connect(
                lambda x: self.pars.__setitem__('upperb', x))
        self.delta_spinbox.valueChanged.connect(
                lambda x: self.pars.__setitem__('delta', x))
        self.usebg_checkbox.stateChanged.connect(
                lambda: self.pars.__setitem__('usebg', 
                    self.usebg_checkbox.isChecked()))

        self.lowerbound_spinbox.editingFinished.connect(self.update)
        self.upperbound_spinbox.editingFinished.connect(self.update)
        self.delta_spinbox.editingFinished.connect(self.update)
        self.usebg_checkbox.stateChanged.connect(self.update)

        self.load_menu.triggered.connect(self.load_menu_slot)

    @pyqtSlot(QAction)
    def load_menu_slot(self, action):
        if action.text() == 'Load h5':
            self.load_h5file()
        elif action.text() == 'Load ASCII':
            self.load_ascii()

    @pyqtSlot(QPoint)
    def show_load_menu(self, pos):
        self.load_menu.exec_(self.load_button.mapToGlobal(pos))

    @pyqtSlot()
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

    @pyqtSlot()
    def reload_h5file(self):
        if self.filepath:
            self.get_h5file_content()
            self.populate_dataset_tree()

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

    @pyqtSlot()
    def load_ascii(self):
        options = QFileDialog.Options()
        # ! use Native dialog or qt dialog... 
        # ! Must be checked on different platforms !

    #   options |= QFileDialog.DontUseNativeDialog
        self.filepaths, _ = QFileDialog.getOpenFileNames(self,
            "Load Text file", "","Text File *.txt *.dat *.asc "
                        "(*.txt *.dat *.asc);;Any File *.* (*.*)", 
            options=options)

        if self.filepaths:
            for f in self.filepaths:
                name = f.split('/')[-1]
                d1 = get_data_from_ascii(f)

                if name not in self.data:
                    self.data[name] = BlackBodySpec(name, **d1)

            self.populate_dataset_tree()

    def get_data_from_tree_item(self, item):
        ''' from item clicked returns the corresponding instance of 
        BlackBodySpec '''
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


    @pyqtSlot()            
    def export_current_raw(self):
        item = self.dataset_tree.currentItem()
        current = self.get_data_from_tree_item(item)

        if current:
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
                        
                # create empty array of len(lam) to be saved in txt
                twocolor_ = np.empty( len(current.lam) )
                # fill with NaN
                twocolor_.fill(np.nan) 

                nans = np.empty(current.pars['delta'])
                nans.fill(np.nan)

                dat1 = np.concatenate([current.twocolor, nans])
                # populate twocolor_ only where data should be, the rest is nan
                twocolor_[current.ind_interval] = dat1

                # we do not export rawwien without BG correction if used. 
                # This may change!
                data_ = np.column_stack((current.lam,
                                         current.planck,
                                         current.wien,
                                         twocolor_))
                np.savetxt(filename, 
                           data_, 
                           delimiter='\t', 
                           comments='',
                           header='lambda\tPlanck\tWien\ttwocolor')

    @pyqtSlot(int)
    def update_delta(self, x):
        self.delta_spinbox.setValue(x)
        self.update()

    @pyqtSlot()
    def choose_delta(self):
        item = self.dataset_tree.currentItem()
        current = self.get_data_from_tree_item(item)

        if current:
            # calculate stdev vs. delta: could be done somewhere else?
            alldeltas = np.array(range(1,300))
            allstddevs = np.array( [np.nanstd(Ph.temp2color(
                                    current.lam[current.ind_interval], 
                                    current.wien[current.ind_interval], 
                                    di)) for di in alldeltas ] )
    
            self.choosedelta_win.set_data(alldeltas, allstddevs)
            self.choosedelta_win.set_vline(current.pars['delta'])
    
            self.choosedelta_win.canvas.draw_idle()
    
            if not self.choosedelta_win.isVisible():
                self.choosedelta_win.show()

    @pyqtSlot()
    def clear_all(self):
        self.filepath = str()
        self.currentfilename_label.setText('')
        self.data = dict()
        self.dataset_tree.clear()
        self.results_table.clearContents()

        self.canvas.clear_all()
        self.choosedelta_win.clear_canvas()

    def eval_fits(self):
        # eval all quantities for a given spectrum
        item = self.dataset_tree.currentItem()
        current = self.get_data_from_tree_item(item)
        try:
            # start with wien to get a reasonable initial value for planck:
            current.eval_wien_fit()
            current.eval_planck_fit()            

            # Refit wien again, accounting for bg obtained in Planck:
            if current.pars['usebg']:
                current.eval_wien_fit()
            # eval two color at the end in all cases
            current.eval_twocolor()

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    @pyqtSlot()
    def update(self):
            item = self.dataset_tree.currentItem()
            current = self.get_data_from_tree_item(item)

            if current:
                # if parameters have changed then we fit again
                # if current was never fitted current.pars is None 
                if not current.pars == self.pars:
                    current.set_pars(self.pars)
                    self.eval_fits()
                
                self.canvas.update_all(current)
                self.results_table.set_values(current)

                # this should update the choose delta window if it stays open!
                # but lead to call again choose_delta after delta update... 
                # not really great
#                if self.choosedelta_win.isVisible():
#                    self.choose_delta()

            else:
                # empty if no data e.g. main item of a serie
                self.canvas.clear_all()
                self.results_table.clearContents()


    @pyqtSlot()
    def batch_fit(self):
        if not self.batch_win.isVisible():
            self.batch_win.show()

        item = self.dataset_tree.currentItem()

        # Group mode:
        if item.childCount() > 0:
            parent_item = item
            nchilds = item.childCount()
        elif item.parent():
            parent_item = item.parent()
            nchilds = parent_item.childCount()
        else:
            nchilds = item.childCount()

        if nchilds > 0: 
            parent_key = parent_item.text(0)
            for i in range(nchilds):
                subitem = parent_item.child(i)
                key = subitem.text(0)
                current = self.data[parent_key][key]

                # will fit all subitems:
                self.dataset_tree.setCurrentItem(subitem)

            self.current_batch = TemperaturesBatch(self.data[parent_key]) 
            self.batch_win.replot(self.current_batch)

        else:
            pass


    @pyqtSlot()
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


        # # diagnoses : 
        # try:
        #     for k, m in self.current_batch.measurements.items():
        #         print(k , ' : ', m.pars)
        # except:
        #     pass