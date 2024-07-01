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
from h5temperature.formats import get_data_from_h5group
from h5temperature.models import BlackBodySpec
from h5temperature.plots import (FourPlotsCanvas,
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
                         delta = 100,
                         usebg = False)

        # left layout   
        load_button = QPushButton('Load h5')
        reload_button = QPushButton('Reload')
        clear_button = QPushButton('Clear')
        exportraw_button = QPushButton('Export current')

        topleftbuttonslayout = QHBoxLayout()
        topleftbuttonslayout.addWidget(load_button)
        topleftbuttonslayout.addWidget(reload_button)

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
        usebg_checkbox = QCheckBox('Use background')

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
        usebg_checkbox.setChecked(self.pars.get('usebg'))

        choosedelta_button = QPushButton('Choose delta')
        fit_button = QPushButton('Fit')

        fitparam_form = QFormLayout()
        fitparam_form.addRow('Lower limit (nm):', lowerbound_spinbox)
        fitparam_form.addRow('Upper limit (nm):', upperbound_spinbox)
        fitparam_form.addRow('2-color delta (px):', self.delta_spinbox)
        

        self.results_table = QTableWidget(7,1)
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
                                                    "epsilon Planck",
                                                    "epsilon Wien", 
                                                    "bg"])

        fit_layout = QVBoxLayout()
        fit_layout.addLayout(fitparam_form)
        fit_layout.addWidget(usebg_checkbox)
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
        self.toolbar.setStyleSheet("font-size: 20px;")
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
        usebg_checkbox.stateChanged.connect(
                lambda: self.pars.__setitem__('usebg', 
                    usebg_checkbox.isChecked()))

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
            "Load HDF5 file", "","HDF5 file (*.h5)", 
            options=options)

        if self.filepath:
            self.get_h5file_content()
            self.populate_dataset_tree()
            self.currentfilename_label.setText(self.filepath.split('/')[-1])

    def reload_h5file(self):
        if self.filepath:
            self.get_h5file_content()
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
                                     current.rawwien,
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
        allstddevs = np.array( [np.nanstd(Ph.temp2color(
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

        self.canvas.clear()
        self.canvas.draw()


    def eval_fits(self, item):
        # eval all quantities for a given spectrum
        current = self.get_data_from_tree_item(item)
        try:
            # start with wien to get a reasonable initial value for planck:
            current.eval_wien_fit()
            current.eval_planck_fit()

            # then refit wien again accounting for bg obtained in Planck:
            if current.pars['usebg']:
                current.eval_wien_fit()              
            
            # eval two color at the end in all cases
            current.eval_twocolor()

        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def update(self, item):
        # If item, otherwise crash
            current = self.get_data_from_tree_item(item)

            self.canvas.clear()

            if current:
                # if parameters have changed then we fit again
                if not current.pars == self.pars:
                    current.set_pars(self.pars)
                    self.eval_fits(item)
                
                # all must be plotted AFTER fit 
                # since wien data can be reevaluated with bg!
                self.plot_data(item)
                self.plot_fits(item)
                self.update_table(item)
            else:
                # empty if no data e.g. main item of a serie
                self.canvas.draw()
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
        self.results_table.setItem(0, 6, 
                    QTableWidgetItem(str( round(current.bg))))


    def plot_data(self, item):
        # plot data
        current = self.get_data_from_tree_item(item)

        self.canvas.axes[0,0].scatter(current.lam, 
                                      current.planck, 
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.4,
                                      s=15, 
                                      zorder=5,
                                      label='Planck data')

        self.canvas.axes[0,1].scatter(1 / current.lam, 
                                      current.wien, 
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.4,
                                      s=15, 
                                      zorder=5,
                                      label='Wien data')

        if current.pars['usebg']:
            self.canvas.axes[0,1].scatter(1 / current.lam, 
                                      current.rawwien, 
                                      edgecolor='k',
                                      facecolor='lightcoral',
                                      alpha=.3,
                                      s=20,
                                      marker='^', 
                                      zorder=3,
                                      label='Wien data (no bg)')

       # self.update_legends()

    def plot_fits(self, item):

        current = self.get_data_from_tree_item(item)

        self.canvas.axes[1,0].scatter(
            current.lam[current.ind_interval][:-current.pars['delta']], 
            current.twocolor, 
            edgecolor='k',
            facecolor='royalblue',
            alpha=.4,
            s=15, 
            zorder=5,
            label='two-color data')

        h_y, h_x, _ = self.canvas.axes[1,1].hist(current.twocolor, 
                                   color='darkblue',
                                   bins = 70,
                                   alpha=.7, 
                                   zorder=5,
                                   label='two-color histogram')

        # plot fits:
        self.canvas.axes[0,0].plot(current.lam[current.ind_interval],
                                   current.planck_fit,
                                   color='r',
                                   linewidth=2,
                                   zorder=7,
                                   label='Planck fit')

        if current.pars['usebg']:
            self.canvas.axes[0,0].axhline(current.bg,
                                          color='k',
                                          linewidth=1.5,
                                          linestyle='dashed',
                                          zorder=3,
                                          label='background')            


        self.canvas.ax_planck_res.scatter(current.lam[current.ind_interval], 
                                          current.planck_residuals, 
                                          edgecolor='gray',
                                          facecolor='none',
                                          linewidth=1.5,
                                          alpha=0.2,
                                          s=15, 
                                          zorder=0,
                                          label='residuals')

        self.canvas.axes[0,1].plot(1 / current.lam[current.ind_interval], 
                                   current.wien_fit, 
                                   c='r', 
                                   linewidth=2, 
                                   zorder=7,
                                   label='Wien fit')

        self.canvas.axes[1,0].axhline(np.mean(current.twocolor), 
                                      color='r',
                                      linestyle='dashed',
                                      zorder=7,
                                      label='mean')            
        
        self.canvas.ax_wien_res.scatter(1 / current.lam[current.ind_interval], 
                                        current.wien_residuals, 
                                        edgecolor='gray',
                                        facecolor='none',
                                        linewidth=1.5,
                                        alpha=0.2,
                                        s=15, 
                                        zorder=0,
                                        label='residuals')

        # texts on plots:
        self.canvas.axes[0,0].text(0.05, 0.65, 
                            'T$_\\mathrm{Planck}$= ' + 
                            str( round(current.T_planck) ) + 
                            ' K', 
                            size=17, 
                            color='r', 
                            zorder=10,
                            transform=self.canvas.axes[0,0].transAxes)

        self.canvas.axes[0,1].text(0.05, 0.65, 
                            'T$_\\mathrm{Wien}$= ' + 
                            str( round(current.T_wien) ) + 
                            ' K', 
                            size=17, 
                            color='r', 
                            zorder=10,
                            transform=self.canvas.axes[0,1].transAxes)
        
        self.canvas.axes[1,0].text(0.2, 0.7, 
                            'T$_\\mathrm{two-color}$= ' + 
                            str( round( current.T_twocolor ) ) + 
                            ' K', 
                            size=17, 
                            color='r', 
                            zorder=10,
                            transform=self.canvas.axes[1,0].transAxes)

        self.canvas.axes[1,1].text(0.05, 0.8, 
                            'std dev. = ' + 
                            str( round( current.T_std_twocolor ) ) + 
                            ' K', 
                            size=17, 
                            color='r', 
                            zorder=10,
                            transform=self.canvas.axes[1,1].transAxes)

        # Custom Autoscales...
        # planck:
        self.canvas.axes[0,0].set_xlim([current.pars['lowerb'] - 100, 
                                        current.pars['upperb'] + 100]) 

        self.canvas.axes[0,0].set_ylim([np.min( current.planck_fit - \
                                            0.4*np.ptp(current.planck_fit)),
                                        np.max( current.planck_fit + \
                                            0.5*np.ptp(current.planck_fit))])

        self.canvas.ax_planck_res.set_ylim([
            np.min( current.planck_residuals ),
            np.max( current.planck_residuals ) ])

        # wien:
        self.canvas.axes[0,1].set_xlim(
            [np.min( 1 / current.lam[current.ind_interval] - 0.0002 ),
             np.max( 1 / current.lam[current.ind_interval] + 0.0002 )])

        self.canvas.axes[0,1].set_ylim([np.min( current.wien_fit - \
                                            0.5*np.ptp(current.wien_fit)),
                                        np.max( current.wien_fit + \
                                            0.5*np.ptp(current.wien_fit))])
        # nanmin/max for cases where I-bg<0:
        self.canvas.ax_wien_res.set_ylim([
            np.nanmin( current.wien_residuals ),
            np.nanmax( current.wien_residuals )])

        # 2color:
        self.canvas.axes[1,0].set_xlim([current.pars['lowerb'] - 20,
                                        current.pars['upperb'] + 10])
        self.canvas.axes[1,0].set_ylim(
            [current.T_twocolor - 5 * current.T_std_twocolor, 
             current.T_twocolor + 5 * current.T_std_twocolor])

        # histogram
        self.canvas.axes[1,1].set_xlim(
            [current.T_twocolor - 5 * current.T_std_twocolor,
             current.T_twocolor + 5 * current.T_std_twocolor])
        self.canvas.axes[1,1].set_ylim([0, np.max(h_y) + .4*np.max(h_y)])

        self.canvas.update_legends()

        # required to have residuals BEHIND data points :
        self.canvas.axes[0,0].set_zorder(2)
        self.canvas.axes[0,0].set_frame_on(False)
        self.canvas.axes[0,1].set_zorder(2)
        self.canvas.axes[0,1].set_frame_on(False)

        self.canvas.draw()
