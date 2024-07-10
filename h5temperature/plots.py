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
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from PyQt5.QtWidgets import (QWidget,
                             QVBoxLayout,
                             QHBoxLayout)
from PyQt5.QtCore import pyqtSignal


class FourPlotsCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):

        self.fig, self.axes = plt.subplots(2, 2, 
                            constrained_layout=True)

        super().__init__(self.fig)

        self.ax_planck_res = self.axes[0,0].twinx()
        self.ax_wien_res = self.axes[0,1].twinx()

        self.create_all()

    def get_NavigationToolbar(self, parent):
        self.navigation_toolbar = NavigationToolbar2QT(self, parent)
        self.navigation_toolbar.setStyleSheet("font-size: 18px;")
        return self.navigation_toolbar
        
    def create_all(self):
        self.create_labels()
        self.create_artists()
        self.create_legends()
        self.create_texts()

        # required to have residuals BEHIND data points :
        self.axes[0,0].set_zorder(2)
        self.axes[0,0].set_frame_on(False)
        self.axes[0,1].set_zorder(2)
        self.axes[0,1].set_frame_on(False)

    def update_all(self, current):
        self.set_data(current)
        self.set_texts(current)
        self.autoscale(current)

        self.draw_idle()

    def clear_all(self):
        self.axes[0,0].clear()
        self.axes[0,1].clear()
        self.axes[1,0].clear()
        self.axes[1,1].clear()
        self.ax_planck_res.clear()
        self.ax_wien_res.clear()

        # re-create all 
        self.create_all()
        self.draw_idle()

    def create_legends(self):
        # legends
        self.axes[0,0].legend(loc='upper left')
        self.ax_planck_res.legend(loc='upper right')
        self.axes[0,1].legend(loc='upper left')   
        self.ax_wien_res.legend(loc='upper right')
        self.axes[1,0].legend() 
        self.axes[1,1].legend()

    def create_labels(self):
        # Planck
        self.axes[0,0].set_xlabel('wavelength (nm)')
        self.axes[0,0].set_ylabel('intensity (arb. unit)')

        self.ax_planck_res.set_ylabel('Planck fit residuals')

        # Wien
        self.axes[0,1].set_xlabel('1/wavelength (1/nm)')
        self.axes[0,1].set_ylabel('Wien')

        self.ax_wien_res.set_ylabel('Wien fit residuals')

        # Two color
        self.axes[1,0].set_xlabel('wavelength (nm)')
        self.axes[1,0].set_ylabel('two-color temperature (K)')

        # Two color Histogram
        self.axes[1,1].set_xlabel('two-color temperature (K)')
        self.axes[1,1].set_ylabel('frequency')

    def create_artists(self):
        self.planck_data_pts = self.axes[0,0].scatter([], [], 
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.4,
                                      s=15, 
                                      zorder=5,
                                      label='Planck data')

        self.wien_data_pts = self.axes[0,1].scatter([], [], 
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.4,
                                      s=15, 
                                      zorder=5,
                                      label='Wien data')

        self.twocolor_data_pts = self.axes[1,0].scatter([], [],
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.4,
                                      s=15, 
                                      zorder=5,
                                      label='two-color data')

        (self.hist_counts, self.hist_bins, 
            self.hist_patches) = self.axes[1,1].hist([],
                                    color='darkblue',
                                    bins = 70,
                                    alpha=.7, 
                                    zorder=5,
                                    label='two-color histogram')

        # plot fits:
        self.planck_fit_line, = self.axes[0,0].plot([], [],
                                   color='r',
                                   linewidth=2,
                                   zorder=7,
                                   label='Planck fit')

        self.planck_res_pts = self.ax_planck_res.scatter([], [], 
                                          edgecolor='gray',
                                          facecolor='none',
                                          linewidth=1.5,
                                          alpha=0.2,
                                          s=15, 
                                          zorder=0,
                                          label='residuals')

        self.wien_fit_line, = self.axes[0,1].plot([], [], 
                                   c='r', 
                                   linewidth=2, 
                                   zorder=7,
                                   label='Wien fit')

        self.wien_res_pts = self.ax_wien_res.scatter([], [], 
                                        edgecolor='gray',
                                        facecolor='none',
                                        linewidth=1.5,
                                        alpha=0.2,
                                        s=15, 
                                        zorder=0,
                                        label='residuals')

        self.twocolor_line = self.axes[1,0].axhline(color='r',
                                      linestyle='dashed',
                                      zorder=7,
                                      label='mean')            

    def create_texts(self):
        self.planck_text = self.axes[0,0].text(0.05, 0.65, 
                            '',
                            size=15, 
                            color='r', 
                            zorder=10,
                            transform=self.axes[0,0].transAxes)

        self.wien_text = self.axes[0,1].text(0.05, 0.65, 
                            '',
                            size=15, 
                            color='r', 
                            zorder=10,
                            transform=self.axes[0,1].transAxes)
        
        self.twocolor_text = self.axes[1,0].text(0.2, 0.7, 
                            '',
                            size=15, 
                            color='r', 
                            zorder=10,
                            transform=self.axes[1,0].transAxes)

        self.twocolor_err_text = self.axes[1,1].text(0.05, 0.8, 
                            '',
                            size=15, 
                            color='r', 
                            zorder=10,
                            transform=self.axes[1,1].transAxes)

    def set_texts(self, current):

        self.planck_text.set_text(
                'T$_{{Planck}}$= {:.0f} K'.format(current.T_planck))
        self.wien_text.set_text(
                'T$_{{Wien}}$= {:.0f} K'.format(current.T_wien))
        self.twocolor_text.set_text(
                'T$_{{two-color}}$= {:.0f} K'.format(current.T_twocolor))
        self.twocolor_err_text.set_text(
                'std. dev = {:.0f} K'.format(current.T_std_twocolor))

    def set_data(self, current):

        self.planck_data_pts.set_offsets(np.c_[current.lam, current.planck])

        self.wien_data_pts.set_offsets(np.c_[1 / current.lam, current.wien])

        self.twocolor_data_pts.set_offsets(
            np.c_[current.lam[current.ind_interval][:-current.pars['delta']], 
            current.twocolor])

        # could be calculated in the model instead of here
        (self.hist_counts, 
            self.hist_bins) = np.histogram(current.twocolor, bins=70)
        # equal-width bins
        dbins = (self.hist_bins[1] - self.hist_bins[0])

        for rect, h, x in zip(self.hist_patches, self.hist_counts, 
                                    self.hist_bins[:-1]):
            rect.set_height(h)
            rect.set_x(x)
            rect.set_width(dbins)

        self.planck_fit_line.set_data(current.lam[current.ind_interval],
                                      current.planck_fit)

        self.planck_res_pts.set_offsets(
            np.c_[current.lam[current.ind_interval], current.planck_residuals])

        self.wien_fit_line.set_data(1 / current.lam[current.ind_interval], 
                                   current.wien_fit)

        self.wien_res_pts.set_offsets(
            np.c_[1 / current.lam[current.ind_interval], 
                current.wien_residuals])

        self.twocolor_line.set_ydata([current.T_twocolor,current.T_twocolor])

    def autoscale(self, current):
        # Custom Autoscales...
        # planck:
        self.axes[0,0].set_xlim([current.pars['lowerb'] - 100, 
                                        current.pars['upperb'] + 100]) 

        self.axes[0,0].set_ylim([np.min( current.planck_fit - \
                                            0.4*np.ptp(current.planck_fit)),
                                        np.max( current.planck_fit + \
                                            0.5*np.ptp(current.planck_fit))])

        self.ax_planck_res.set_ylim([
            np.min( current.planck_residuals ),
            np.max( current.planck_residuals ) ])

        # wien:
        self.axes[0,1].set_xlim(
            [np.min( 1 / current.lam[current.ind_interval] - 0.0002 ),
             np.max( 1 / current.lam[current.ind_interval] + 0.0002 )])

        self.axes[0,1].set_ylim([np.min( current.wien_fit - \
                                            0.5*np.ptp(current.wien_fit)),
                                        np.max( current.wien_fit + \
                                            0.5*np.ptp(current.wien_fit))])

        self.ax_wien_res.set_ylim([
            np.min( current.wien_residuals ),
            np.max( current.wien_residuals )])

        # 2color:
        self.axes[1,0].set_xlim([current.pars['lowerb'] - 20,
                                        current.pars['upperb'] + 10])
        self.axes[1,0].set_ylim(
            [current.T_twocolor - 5 * current.T_std_twocolor, 
             current.T_twocolor + 5 * current.T_std_twocolor])

        # histogram
        self.axes[1,1].set_xlim(
            [current.T_twocolor - 5 * current.T_std_twocolor,
             current.T_twocolor + 5 * current.T_std_twocolor])

        self.axes[1,1].set_ylim([0, 1.4*np.max(self.hist_counts)])



class SinglePlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(
            constrained_layout=True)

        super().__init__(self.fig)



class ChooseDeltaWindow(QWidget):

    delta_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.resize(500,400)

        self.setWindowTitle('Choose delta...')

        self.canvas = SinglePlotCanvas(self)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)     
        self.toolbar.setStyleSheet("font-size: 18px;")

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

        self.create_labels()
        self.create_artists()

        # click event
        self.canvas.mpl_connect('button_press_event', self.choose)


    def create_labels(self):
        self.canvas.ax.set_xlabel('delta (px)')
        self.canvas.ax.set_ylabel('two-color temperature std deviation (K)')

        # fixed limits
        self.canvas.ax.set_xlim([0,300])
        self.canvas.ax.set_ylim([0,3e3])

    def create_artists(self):
        self.choosedelta_pts = self.canvas.ax.scatter([], [],
                                               marker='X',
                                               edgecolor='k',
                                               color='royalblue',
                                               alpha=0.5,
                                               s=30)
        self.choosedelta_line = self.canvas.ax.axvline(color='k',
                                               linestyle='dashed',
                                               linewidth=1)

    def set_data(self, x, y):
        self.choosedelta_pts.set_offsets(np.c_[x, y])

    def set_vline(self, x):
        self.choosedelta_line.set_xdata([x])

    def choose(self, event):
        x = int(event.xdata)
        self.set_vline(x)
        
        self.delta_changed.emit(x)
        self.canvas.draw_idle()

    def clear_canvas(self):
        self.canvas.ax.clear()
        self.create_labels()
        self.create_artists()
        self.canvas.draw_idle()