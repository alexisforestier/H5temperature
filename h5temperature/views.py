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


class FourPlotsCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):

        self.fig, self.axes = plt.subplots(2, 2, 
                            constrained_layout=True)

        super(FourPlotsCanvas, self).__init__(self.fig)

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

        self.init_plot_artists()


    def get_NavigationToolbar(self, parent):
        return NavigationToolbar2QT(self, parent)


    def update_legends(self):
        # legends
        self.axes[0,0].legend(loc='upper left')
        self.ax_planck_res.legend(loc='upper right')
        self.axes[0,1].legend(loc='upper left')   
        self.ax_wien_res.legend(loc='upper right')
        self.axes[1,0].legend() 
        self.axes[1,1].legend()


    def clear(self):
        self.axes[0,0].clear()
        self.axes[0,1].clear()
        self.axes[1,0].clear()
        self.axes[1,1].clear()
        self.ax_planck_res.clear()
        self.ax_wien_res.clear()


    def init_plot_artists(self):

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

        _, _, self.hist_patches = self.axes[1,1].hist([],
                                          color='darkblue',
                                          bins = 70,
                                          alpha=.7, 
                                          zorder=5,
                                          label='two-color histogram')


        # # plot fits:
        # self.canvas.axes[0,0].plot(current.lam[current.ind_interval],
        #                            current.planck_fit,
        #                            color='r',
        #                            linewidth=2,
        #                            zorder=7,
        #                            label='Planck fit')

        # self.canvas.ax_planck_res.scatter(current.lam[current.ind_interval], 
        #                                   current.planck_residuals, 
        #                                   edgecolor='gray',
        #                                   facecolor='none',
        #                                   linewidth=1.5,
        #                                   alpha=0.2,
        #                                   s=15, 
        #                                   zorder=0,
        #                                   label='residuals')

        # self.canvas.axes[0,1].plot(1 / current.lam[current.ind_interval], 
        #                            current.wien_fit, 
        #                            c='r', 
        #                            linewidth=2, 
        #                            zorder=7,
        #                            label='Wien fit')

        # self.canvas.axes[1,0].axhline(np.mean(current.twocolor), 
        #                               color='r',
        #                               linestyle='dashed',
        #                               zorder=7,
        #                               label='mean')            
        
        # self.canvas.ax_wien_res.scatter(1 / current.lam[current.ind_interval], 
        #                                 current.wien_residuals, 
        #                                 edgecolor='gray',
        #                                 facecolor='none',
        #                                 linewidth=1.5,
        #                                 alpha=0.2,
        #                                 s=15, 
        #                                 zorder=0,
        #                                 label='residuals')

    def set_data(self, current):

        self.planck_data_pts.set_offsets(np.c_[current.lam, current.planck])

        self.wien_data_pts.set_offsets(np.c_[1 / current.lam, current.wien])

        self.twocolor_data_pts.set_offsets(
            np.c_[current.lam[current.ind_interval][:-current.pars['delta']], 
            current.twocolor])

        counts, bins = np.histogram(current.twocolor, bins=70)
        dbins = bins[1] - bins[0]

        for rect, h in zip(self.hist_patches, counts):
            rect.set_height(h)
        for rect, x in zip(self.hist_patches, bins[:-1]):
            rect.set_x(x)
            rect.set_width(bins[1]-bins[0])

        self.axes[1,1].set_ylim([0, 1.4*np.max(counts)])



class ChooseDeltaPlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(
            constrained_layout=True)

        self.ax.set_xlabel('delta (px)')
        self.ax.set_ylabel('two-color temperature std deviation (K)')

        super(ChooseDeltaPlotCanvas, self).__init__(self.fig)


class ChooseDeltaWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.resize(500,400)

        self.setWindowTitle('Choose delta...')

        self.canvas = ChooseDeltaPlotCanvas(self)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)     
        self.toolbar.setStyleSheet("font-size: 18px;")

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)