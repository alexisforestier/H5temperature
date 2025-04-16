#   Copyright (C) 2023-2025 Alexis Forestier (alforestier@gmail.com)
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

import os
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
from PyQt5.QtGui import QIcon, QPixmap

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
        # constructs the full path to "resources"
        self.icon_path = os.path.join(os.path.dirname(
                                os.path.abspath(__file__)),
                         'resources/h5temp.png')
        self.setWindowIcon(QIcon(self.icon_path))

        self.resize(1600,900)

        # data stored in MainWindow
        self.filepath = str()
        self.data = dict()
        self.batch = None   # No batch by default
        self.autofit = True # <- automatic fit or not

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
        self.autofit_checkbox = QCheckBox('Auto Fit')

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
        self.autofit_checkbox.setChecked(self.autofit)

        self.choosedelta_button = QPushButton('Choose delta')
        self.fit_button = QPushButton('Fit')
        self.batch_fit_button = QPushButton('Batch fit')

        self.batch_menu = QMenu(self)
        self.batch_menu.addAction(QAction("Current group (default)", self))
        # not implemented yet:
#        self.batch_menu.addAction(QAction("Select", self))
        self.batch_menu.addAction(QAction("All", self))

        fitparam_form = QFormLayout()
        fitparam_form.addRow('Lower limit (nm):', self.lowerbound_spinbox)
        fitparam_form.addRow('Upper limit (nm):', self.upperbound_spinbox)
        fitparam_form.addRow('2-color delta (px):', self.delta_spinbox)
        
        self.results_table = SingleFitResultsTable()

        self.export_results_button = QPushButton('Export all results')

        fit_layout = QVBoxLayout()
        fit_layout.addLayout(fitparam_form)
        fit_layout.addWidget(self.usebg_checkbox)
        fit_layout.addWidget(self.choosedelta_button)
        fit_layout.addWidget(self.autofit_checkbox)
        fit_layout.addWidget(self.fit_button)
        fit_layout.addWidget(self.batch_fit_button)
        fit_layout.addWidget(self.results_table)
        fit_layout.addWidget(self.export_results_button)
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

        # setup other windows
        # self is passed as parent window
        self.choosedelta_win = ChooseDeltaWindow(self)
        self.batch_win = BatchWindow(self)

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

        self.load_button.clicked.connect(self.load_h5file)
        self.load_button.setContextMenuPolicy(Qt.CustomContextMenu)       
        self.load_button.customContextMenuRequested.connect(
                lambda pos: self.show_any_menu(pos, self.load_button, 
                                                   self.load_menu))

        self.reload_button.clicked.connect(self.reload_h5file)
        self.clear_button.clicked.connect(self.clear_all)
        self.about_button.clicked.connect(self.show_about)

        self.exportraw_button.clicked.connect(self.export_current_raw)

        self.dataset_tree.currentItemChanged.connect(
            lambda: self.update('dataset_tree'))
        self.fit_button.clicked.connect(
            lambda: self.update('fit_button'))
        
        # default behaviour:
        self.batch_fit_button.clicked.connect(
            lambda: self.batch_fit(QAction("Current group (default)", self)))

        self.batch_fit_button.setContextMenuPolicy(Qt.CustomContextMenu)       
        self.batch_fit_button.customContextMenuRequested.connect(
                lambda pos: self.show_any_menu(pos, self.batch_fit_button, 
                                                   self.batch_menu))

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
        self.autofit_checkbox.stateChanged.connect(
                lambda b: setattr(self, 'autofit', bool(b)))

        self.export_results_button.clicked.connect(self.export_results)

#        self.lowerbound_spinbox.editingFinished.connect(self.update)
#        self.upperbound_spinbox.editingFinished.connect(self.update)
#        self.delta_spinbox.editingFinished.connect(self.update)
#        self.usebg_checkbox.stateChanged.connect(self.update)

        self.load_menu.triggered.connect(self.load_menu_slot)
        self.batch_menu.triggered.connect(self.batch_fit)

    @pyqtSlot(QAction)
    def load_menu_slot(self, action):
        if action.text() == 'Load h5':
            self.load_h5file()
        elif action.text() == 'Load ASCII':
            self.load_ascii()

    @pyqtSlot(QPoint, QWidget, QMenu)
    def show_any_menu(self, pos, clicked_widget, menu):
        menu.exec_(clicked_widget.mapToGlobal(pos))

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
                                    subnam = ''.join([nam, '[{}]'.format(i)])
                                    # use names for referencing
                                    self.data[nam][subnam] = \
                                                BlackBodySpec(subnam, **di)

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
            d = get_data_from_ascii(self.filepaths)
            for di in d:
                self.data[di['name']] = BlackBodySpec(**di)
            
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
                    firstelem = self.data[k][list(self.data[k].keys())[0]]
                    return firstelem.timestamp
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
        self.update('choose_delta')

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
            else:
                self.choosedelta_win.activateWindow()

    @pyqtSlot()
    def clear_all(self):
        self.filepath = str()
        self.currentfilename_label.setText('')
        self.data = dict()
        self.dataset_tree.clear()
        self.results_table.clearContents()
        self.batch = None

        self.canvas.clear_all()
        self.choosedelta_win.clear_canvas()

    def eval_fits(self, current):

        if not current.pars == self.pars:
            current.set_pars(self.pars)
            # eval all quantities for a given spectrum
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


    @pyqtSlot(str)
    def update(self, called_from):

        item = self.dataset_tree.currentItem()
        current = self.get_data_from_tree_item(item)

        # clear all plots and fit results table:
        self.canvas.clear_all()
        self.results_table.clearContents()

        if current:            
            # if autofit, or not called from fit button/delta_changed
            # we do the fit:
            if self.autofit or (not called_from == 'dataset_tree'):
                self.eval_fits(current)

            if current._fitted:
                self.canvas.update_fits(current)
                self.results_table.set_values(current)

            # in all cases we plot data:
            self.canvas.update_data(current)
            
            # propagate change to the batch widget:
            # current.name is always the parent name in the group, this may change
            # or a class for groups ?  
            if self.batch and (item.text(0) in self.batch.keys):
                self.batch.extract_all()
                self.batch_win.replot(self.batch)

        # no item selected:
        else:
            #empty if no data e.g. main item of a serie
            self.canvas.clear_all()
            self.results_table.clearContents()
        # this should update the choose delta window if it stays open!
        # but lead to call again choose_delta after delta update... 
        # not really great
#        if self.choosedelta_win.isVisible():
#            self.choose_delta()

#    @pyqtSlot()
#    def update_fit():

    @pyqtSlot(QAction)
    def batch_fit(self, action):
        # show the batch window        
        if not self.batch_win.isVisible():
            self.batch_win.show()
        else:
            self.batch_win.activateWindow()

        keys_to_fit = dict()

        # Group mode:
        if action.text() == "Current group (default)":
            item = self.dataset_tree.currentItem()
            if item:
                # item is the parent:
                if item.childCount() > 0:
                    parent_item = item
                    parent_item.setExpanded(True)
                # item is a child:
                elif item.parent():
                    parent_item = item.parent()
                    nchilds = parent_item.childCount()
                # No Group Batch possible
                else:
                    parent_item = None
    
                if parent_item:
                    parent_item_key = parent_item.text(0)
                    nchilds = parent_item.childCount()
    
                    keys_to_fit[parent_item_key] = list()
    
                    for i in range(nchilds):
                        child_key = parent_item.child(i).text(0)
                        keys_to_fit[parent_item_key].append(child_key)

        elif action.text() == "All":
            # loop over items of the dataset_tree as a tip to maintain ordering
            # not ideal but works
            ntoplevel = self.dataset_tree.topLevelItemCount()

            for ind in range(ntoplevel):
                toplevel_item = self.dataset_tree.topLevelItem(ind)
                toplevel_item_key = toplevel_item.text(0)
                # group
                if toplevel_item.childCount() > 0:
                    nchilds = toplevel_item.childCount()
                    keys_to_fit[toplevel_item_key] = list()

                    for i in range(nchilds):
                        child_key = toplevel_item.child(i).text(0)
                        keys_to_fit[toplevel_item_key].append(child_key)
                else:
                    # single measurement
                    keys_to_fit[toplevel_item_key] = toplevel_item_key

        # eval all fits and create batch_data from keys_to_fit
        # General to all modes
        if len(keys_to_fit) > 0:
            batch_data = list()
            for k, subks in keys_to_fit.items():
                # single measurement case:
                if isinstance(subks, str):
                    current = self.data[k]
                    self.eval_fits(current)
                    batch_data.append(current)
                # group case:
                else:
                    for subk in subks:
                        current = self.data[k][subk]
                        # fit all subitems !
                        self.eval_fits(current)
                        batch_data.append(current)

            self.batch = TemperaturesBatch(batch_data)
            self.batch_win.replot(self.batch)
        else:
            QMessageBox.critical(self, 'Error',
            'Nothing to process in batch')

    @pyqtSlot()
    def export_results(self):
        options =  QFileDialog.Options() 
        #options = QFileDialog.DontUseNativeDialog
        # ! Must be checked on different platforms !
        filename, filetype = \
            QFileDialog.getSaveFileName(self,
                                        "h5temperature: Export all results", 
                                        "",
                                        "Text File (*.txt);;All Files (*)", 
                                        options=options)
        if filename:
            if filetype == 'Text File (*.txt)':
                if '.txt' in filename:
                    pass
                else:
                    filename += '.txt'

            lines = []
            ntoplevel = self.dataset_tree.topLevelItemCount()
            # loop over items of the dataset_tree as a tip to maintain ordering
            # not ideal but works
            for ind in range(ntoplevel):
                toplevel_item = self.dataset_tree.topLevelItem(ind)
                toplevel_item_key = toplevel_item.text(0)
    
                if toplevel_item.childCount() > 0:
                    nchilds = toplevel_item.childCount()
                    for i in range(nchilds):
                        child_key = toplevel_item.child(i).text(0)
                        current = self.data[toplevel_item_key][child_key]
                        lines.append(current.get_fit_results())
                else:
                    current = self.data[toplevel_item_key]
                    lines.append(current.get_fit_results())
    
            header = '\t'.join(list(lines[0].keys()))
            out = [list(l.values()) for l in lines]

            np.savetxt(filename, 
               out, 
               delimiter='\t', 
               comments='',
               fmt='%s',
               header=header)
        else:
            QMessageBox.critical(self, 'Error',
            'No file specified')

    @pyqtSlot()
    def show_about(self):
        text = '<center>' \
               '<h1> h5temperature </h1>' \
               '<h2> version {}</h2>'.format(__version__) + '<br>' \
               'Analysis methods used in h5temperature are detailed in: ' \
               '<a href=\"https://doi.org/10.1080/08957950412331331718\">' \
               'Benedetti and Loubeyre (2004), ' \
               'High Pressure Research, 24:4, 423-445</a> <br><br>' \
               'Copyright 2023-2025 Alexis Forestier ' \
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

        logo = QPixmap(self.icon_path).scaled(128,128,Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation)

        msg = QMessageBox(self)
        msg.setWindowTitle("About h5temperature")
        msg.setText(text)
        msg.setIconPixmap(logo)

        msg.setStyleSheet("background-color: white;")
        msg.exec_()