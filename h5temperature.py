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

import sys
import numpy as np
import h5py
from scipy.optimize import curve_fit
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
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
                             QListWidget,
                             QFormLayout,
                             QVBoxLayout,
                             QHBoxLayout,
                             QFileDialog,
                             QMessageBox,
                             QSizePolicy)

from h5temperaturePhysics import temp2color
from h5temperatureModels import BlackBodyFromh5
from h5temperatureAbout import AboutWindow

__version__ = '0.2'

class SinglePlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig, self.ax = matplotlib.pyplot.subplots(
            constrained_layout=True)

        self.ax.set_xlabel('delta (px)')
        self.ax.set_ylabel('two-color temperature std deviation (K)')

        super(SinglePlotCanvas, self).__init__(self.fig)


class ChooseDeltaWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.resize(500,400)

        self.setWindowTitle('Choose delta...')

        self.canvas = SinglePlotCanvas(self)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)     
        self.toolbar.setStyleSheet("font-size: 16px;")
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)


class PlotsCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):

        self.fig, self.axes = matplotlib.pyplot.subplots(2, 2, 
                            constrained_layout=True)

        # Planck
        self.axes[0,0].set_xlabel('wavelength (nm)')
        self.axes[0,0].set_ylabel('intensity (arb. unit)')
        self.ax_planck_res = self.axes[0,0].twinx()
        self.ax_planck_res.set_ylabel('Planck fit residuals')

        # Wien
        self.axes[0,1].set_xlabel('1/wavelength (1/nm)')
        self.axes[0,1].set_ylabel('Wien')
        self.ax_wien_res = self.axes[0,1].twinx()
        self.ax_wien_res.set_ylabel('Wien fit residuals')

        # Two color
        self.axes[1,0].set_xlabel('wavelength (nm)')
        self.axes[1,0].set_ylabel('two-color temperature (K)')

        # Two color Histogram
        self.axes[1,1].set_xlabel('two-color temperature (K)')
        self.axes[1,1].set_ylabel('frequency')

        super(PlotsCanvas, self).__init__(self.fig)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('h5temperature {}'.format(__version__))
        self.resize(1400,800)

        # data stored in self
        self.filepath = str()
        self.data = dict()

        # parameters and their default values
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

        self.dataset_list = QListWidget()
        self.dataset_list.setSelectionMode(1) # single selection

        leftlayout = QVBoxLayout()
        leftlayout.addLayout(topleftbuttonslayout)
        leftlayout.addLayout(currentfile_layout)
        leftlayout.addWidget(self.dataset_list)
        leftlayout.addWidget(clear_button)
        leftlayout.addWidget(exportraw_button)

        left_groupbox = QGroupBox('Data')
        left_groupbox.setLayout(leftlayout)

        left_groupbox.setMinimumWidth(230)

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
        
        # default values:
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
                                          'font-weight: bold}')
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
        right_groupbox.setMinimumWidth(200)

        # center layout
        center_groupbox = QGroupBox()
        center_groupbox.setStyleSheet('QGroupBox  {border: 2px solid gray;\
                                                background-color: white;}')
        plot_layout = QVBoxLayout()

        # set empty plots
        self.canvas = PlotsCanvas(self)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setStyleSheet("font-size: 16px;")
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)

        center_groupbox.setLayout(plot_layout)

        # setup choosedelta window
        self.choosedelta_win = ChooseDeltaWindow()
        self.choosedelta_win.setStyleSheet("background-color: white")

        # setup about window
        self.about_win = AboutWindow()

        # add the about button
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

        # CONNECTS

        about_button.clicked.connect(self.show_about)
        load_button.clicked.connect(self.load_h5file)
        reload_button.clicked.connect(self.reload_h5file)
        clear_button.clicked.connect(self.clear_all)

        exportraw_button.clicked.connect(
        lambda: \
            self.export_current_raw(self.dataset_list.currentItem().text()))

        choosedelta_button.clicked.connect(
        lambda: \
            self.choose_delta( self.dataset_list.currentItem().text() ))

        lowerbound_spinbox.valueChanged.connect(
                lambda x: self.pars.__setitem__('lowerb', x))
        upperbound_spinbox.valueChanged.connect(
                lambda x: self.pars.__setitem__('upperb', x))
        self.delta_spinbox.valueChanged.connect(
                lambda x: self.pars.__setitem__('delta', x))
        usebg_checkbox.stateChanged.connect(
                lambda: self.pars.__setitem__('usebg', 
                    usebg_checkbox.isChecked()))

        self.dataset_list.currentTextChanged.connect(self.update)

        fit_button.clicked.connect(lambda: 
            self.update( self.dataset_list.currentItem().text()) )

    def show_about(self):
        self.about_win.show()


    def get_h5file_content(self):
        # read h5 file and store in self.data: 
        with h5py.File(self.filepath, 'r') as file:
            for nam, dat in file.items():
            # /!\ when hdf5 files are open in another thread
            # it seems to lead to None in the entire subgroup...
            # this will need to be checked again...:
            # Can the last measured T be opened or not on the beamline?
                if dat is not None: 
                # get temperature measurements only
                    if 'measurement/T_planck' in dat:
                    # not already loaded only:
                        if nam not in self.data:
                        # populate data:
                            self.data[nam] = BlackBodyFromh5(dat, nam)

    def populate_dataset_list(self):
        if self.data:
            try:
                # sort datasets in chronological order
                names_chrono = sorted(self.data.keys(), 
                            key = lambda k: self.data[k].timestamp)
            except:
                QMessageBox.warning(self, 'Warning',
                'Problem parsing measurement dates and times.\n'
                'Chronological order will NOT be used.')     

                names_chrono = self.data.keys()
            
            prev_items = [self.dataset_list.item(x).text() 
                    for x in range(self.dataset_list.count())]
            # new items will always be added at the end
            # thus data are in chronological order within 
            # a given h5 loaded but not globally. 
            for n in names_chrono:
                if n not in prev_items:
                    self.dataset_list.addItem(n)

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
            self.populate_dataset_list()
            self.currentfilename_label.setText(self.filepath.split('/')[-1])

    def reload_h5file(self):
        if self.filepath:
            self.get_h5file_content()
            self.populate_dataset_list()

    def export_current_raw(self, nam):
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
    
            current = self.data[nam]

            # create empty array of len(lam) to be saved in txt
            twocolor_ = np.empty( len(current.lam) )
            # fill with NaN
            twocolor_.fill(np.nan) 

            nans = np.empty(current.pars['delta'])
            nans.fill(np.nan)

            dat1 = np.concatenate([current.twocolor, nans])
            # populate twocolor_ only where data should be, the rest is nan
            twocolor_[current._ininterval] = dat1

            data_ = np.column_stack((current.lam,
                                     current.planck,
                                     current.rawwien,
                                     twocolor_))
            np.savetxt(filename, 
                       data_, 
                       delimiter='\t', 
                       comments='',
                       header='lambda\tPlanck\tWien\ttwocolor')


    def choose_delta(self, nam):

        current = self.data[nam]

        _ = [c.remove() for c in self.choosedelta_win.canvas.ax.collections]
        _ = [l.remove() for l in self.choosedelta_win.canvas.ax.lines]
        #self.choosedelta_win.canvas.ax.collections.clear()

        alldeltas = np.array(range(300))
        allstddevs = np.array( [np.nanstd(temp2color(
                                current.lam[current._ininterval], 
                                current.wien[current._ininterval], 
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
            
            self.update(nam)
            
        # click event
        self.choosedelta_win.canvas.mpl_connect('button_press_event', 
                            get_xclick)


    def clear_all(self):
        self.filepath = str()
        self.currentfilename_label.setText('')
        self.data = dict()
        self.dataset_list.clear()

        self.clear_plots()
        self.canvas.draw()

    def clear_plots(self):
        # clear previous data on plots

        # seems to be necessary to loop since new version of matplotlib..
        _ = [c.remove() for c in self.canvas.axes[0,0].collections]
        _ = [c.remove() for c in self.canvas.axes[0,1].collections]
        _ = [c.remove() for c in self.canvas.axes[1,0].collections]
        #self.canvas.axes[0,0].collections.clear()
        #self.canvas.axes[0,1].collections.clear()
        #self.canvas.axes[1,0].collections.clear()
        
        # to remove histogram bars:
        _ = [b.remove() for b in self.canvas.axes[1,1].containers]

        _ = [c.remove() for c in self.canvas.ax_planck_res.collections]
        _ = [c.remove() for c in self.canvas.ax_wien_res.collections]
        
        #self.canvas.ax_planck_res.collections.clear()
        #self.canvas.ax_wien_res.collections.clear()

        
        _ = [l.remove() for l in self.canvas.axes[0,0].lines]
        _ = [l.remove() for l in self.canvas.axes[0,1].lines]
        _ = [l.remove() for l in self.canvas.axes[1,0].lines]
        _ = [l.remove() for l in self.canvas.axes[1,1].lines]
        #self.canvas.axes[0,0].lines.clear()
        #self.canvas.axes[0,1].lines.clear()
        #self.canvas.axes[1,0].lines.clear()
        #self.canvas.axes[1,1].lines.clear()

        _ = [t.remove() for t in self.canvas.axes[0,0].texts]
        _ = [t.remove() for t in self.canvas.axes[0,1].texts]
        _ = [t.remove() for t in self.canvas.axes[1,0].texts]
        _ = [t.remove() for t in self.canvas.axes[1,1].texts]
        #self.canvas.axes[0,0].texts.clear()
        #self.canvas.axes[0,1].texts.clear()
        #self.canvas.axes[1,0].texts.clear()
        #self.canvas.axes[1,1].texts.clear()

    def eval_fits(self, nam):
        # eval all quantities for a given spectrum
        current = self.data[nam]
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

    def update(self, nam):
        # If nam otherwise crash
        if nam:
            current = self.data[nam]

            self.clear_plots()

            # if parameters have changed then we fit again
            if not current.pars == self.pars:
                current.set_pars(self.pars)
                self.eval_fits(nam)
            
            # all must be plotted AFTER fit 
            # since wien data can be reevaluated with bg!
            self.plot_data(nam)
            self.plot_fits(nam)
            self.update_table(nam)

    def update_table(self, nam):
        current = self.data[nam]
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

    def plot_data(self, nam):
        # plot data
        current = self.data[nam]

        self.canvas.axes[0,0].scatter(current.lam, 
                                      current.planck, 
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.5,
                                      s=15, 
                                      zorder=5,
                                      label='Planck data')

        self.canvas.axes[0,1].scatter(1 / current.lam, 
                                      current.wien, 
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.5,
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

    def plot_fits(self, nam):

        current = self.data[nam]

        self.canvas.axes[1,0].scatter(
            current.lam[current._ininterval][:-current.pars['delta']], 
            current.twocolor, 
            edgecolor='k',
            facecolor='royalblue',
            alpha=.5,
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
        self.canvas.axes[0,0].plot(current.lam[current._ininterval],
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


        self.canvas.ax_planck_res.scatter(current.lam[current._ininterval], 
                                          current.planck_residuals, 
                                          edgecolor='gray',
                                          facecolor='none',
                                          linewidth=1.5,
                                          alpha=0.3,
                                          s=15, 
                                          zorder=0,
                                          label='residuals')

        self.canvas.axes[0,1].plot(1 / current.lam[current._ininterval], 
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
        
        self.canvas.ax_wien_res.scatter(1 / current.lam[current._ininterval], 
                                        current.wien_residuals, 
                                        edgecolor='gray',
                                        facecolor='none',
                                        linewidth=1.5,
                                        alpha=0.3,
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
                                            0.5*np.ptp(current.planck_fit)),
                                        np.max( current.planck_fit + \
                                            0.5*np.ptp(current.planck_fit))])

        self.canvas.ax_planck_res.set_ylim([
            np.min( current.planck_residuals ),
            np.max( current.planck_residuals ) ])

        # wien:
        self.canvas.axes[0,1].set_xlim(
            [np.min( 1 / current.lam[current._ininterval] - 0.0002 ),
             np.max( 1 / current.lam[current._ininterval] + 0.0002 )])

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

        self.update_legends()

        # required to have residuals BEHIND data points :
        self.canvas.axes[0,0].set_zorder(2)
        self.canvas.axes[0,0].set_frame_on(False)
        self.canvas.axes[0,1].set_zorder(2)
        self.canvas.axes[0,1].set_frame_on(False)

        self.canvas.draw()


    def update_legends(self):
        # legends
        self.canvas.axes[0,0].legend(loc='upper left')
        self.canvas.ax_planck_res.legend(loc='upper right')
        self.canvas.axes[0,1].legend(loc='upper left')   
        self.canvas.ax_wien_res.legend(loc='upper right')
        self.canvas.axes[1,0].legend() 
        self.canvas.axes[1,1].legend()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    app.exec()