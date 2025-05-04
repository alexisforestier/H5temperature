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


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from PyQt5.QtWidgets import (QWidget,
                             QVBoxLayout,
                             QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal


class FourPlotsCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):

        self.fig, self.axes = plt.subplots(2, 2, constrained_layout=True)

        super().__init__(self.fig)

        self.ax_planck_res = self.axes[0,0].twinx()
        self.ax_wien_res = self.axes[0,1].twinx()

        self.create_all()

    def get_NavigationToolbar(self, parent):
        self.navigation_toolbar = NavigationToolbar2QT(self, parent)
        self.navigation_toolbar.setStyleSheet("font-size: 18px;")
        return self.navigation_toolbar
        
    def create_all(self):
        self.create_artists()
        self.create_labels()
        self.create_legends()
        self.create_texts()

        # required to have residuals BEHIND data points :
        self.axes[0,0].set_zorder(2)
        self.axes[0,0].set_frame_on(False)
        self.axes[0,1].set_zorder(2)
        self.axes[0,1].set_frame_on(False)

    def update_fits(self, current):
#        self.set_data(current)   # already called in mainwindow through 
                                  # updatedata 
        self.set_fits(current)
        self.set_fitslim(current)
        self.set_texts(current)
        self.autoscale(current)

        self.draw_idle()

    def update_data(self, current):
        self.set_data(current)
        self.autoscale(current)

        self.draw_idle()

    def update_all(self, current):
        self.set_data(current)
        self.set_fits(current)
        self.set_texts(current)
        self.autoscale(current)

        self.draw_idle()       

    def clear_all(self):
        self.ax_planck_res.clear()
        self.ax_wien_res.clear()
        self.axes[0,0].clear()
        self.axes[0,1].clear()
        self.axes[1,0].clear()
        self.axes[1,1].clear()

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

        # fix for a matplotlib bug?
        # https://github.com/matplotlib/matplotlib/issues/28268
        self.ax_planck_res.yaxis.set_label_position('right') 
        self.ax_wien_res.yaxis.set_label_position('right') 

    def create_artists(self):
        self.planck_data_pts = self.axes[0,0].scatter([], [], 
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.3,
                                      s=15, 
                                      zorder=5,
                                      label='Planck data')
        
        self.wien_data_pts = self.axes[0,1].scatter([], [], 
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.3,
                                      s=15, 
                                      zorder=5,
                                      label='Wien data')

        self.rawwien_data_pts = self.axes[0,1].scatter([], [], 
                                      edgecolor='k',
                                      facecolor='lightcoral',
                                      marker='^',
                                      alpha=.3,
                                      s=15, 
                                      zorder=0,
                                      label='Wien data (no bg)')

        self.twocolor_data_pts = self.axes[1,0].scatter([], [],
                                      edgecolor='k',
                                      facecolor='royalblue',
                                      alpha=.3,
                                      s=15, 
                                      zorder=5,
                                      label='two-color data')

        (self.hist_counts, self.hist_bins, 
            self.hist_patches) = self.axes[1,1].hist([],
                                    color='darkblue',
                                    bins = 70,
                                    alpha=.5, 
                                    zorder=5,
                                    label='two-color histogram')

        # plot fits:
        self.planck_fit_line, = self.axes[0,0].plot([], [],
                                   color='r',
                                   linewidth=2.5,
                                   zorder=7,
                                   label='Planck fit')

        self.planck_bg = self.axes[0,0].axhline(0,
                                      color='k',
                                      linewidth=1.5,
                                      linestyle='dashed',
                                      zorder=3,
                                      label='background')            

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
                                   linewidth=2.5, 
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
                                      linewidth=2.5,
                                      zorder=7,
                                      label='mean')            

        self.planck_lowlim_line = self.axes[0,0].axvline(
                                      color='g',
                                      linewidth=0.8,
                                      linestyle='solid',
                                      zorder=3)

        self.planck_highlim_line = self.axes[0,0].axvline(
                                      color='g',
                                      linewidth=0.8,
                                      linestyle='solid',
                                      zorder=3)

        self.wien_lowlim_line = self.axes[0,1].axvline(
                                      color='g',
                                      linewidth=0.8,
                                      linestyle='solid',
                                      zorder=3)

        self.wien_highlim_line = self.axes[0,1].axvline(
                                      color='g',
                                      linewidth=0.8,
                                      linestyle='solid',
                                      zorder=3)

        self.saturation_rect = patches.Rectangle((0.5, 0.5), 0, 0, 
            linewidth=0, edgecolor='None', facecolor='r', alpha=0.4)

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
                    'T$_{{two\\mathrm{{-}}color}}$= {:.0f} K'.format(current.T_twocolor))
        self.twocolor_err_text.set_text(
                    'std. dev = {:.0f} K'.format(current.T_std_twocolor))

    def set_data(self, current):

        self.planck_data_pts.set_offsets(np.c_[current.lam, current.planck])
        self.wien_data_pts.set_offsets(np.c_[1 / current.lam, current.wien])

        if current._saturated:
            rect_xmin = np.min( current.lam[current.saturated_ind] )
            rect_ymin = np.min( current.planck[current.saturated_ind] )
            rect_w = np.ptp( current.lam[current.saturated_ind] )
            rect_h = np.ptp( current.planck[current.saturated_ind] )
            self.saturation_rect.set_xy((rect_xmin, rect_ymin))
            self.saturation_rect.set_width(rect_w)
            self.saturation_rect.set_height(rect_h)

            self.axes[0,0].add_patch(self.saturation_rect)

        else:
            self.saturation_rect.set_width(0)
            self.saturation_rect.set_height(0)            

    def set_fits(self, current):

        self.twocolor_data_pts.set_offsets(
            np.c_[current.lam[current.ind_interval][:-current.pars['delta']], 
                  current.twocolor])

        # could be calculated in the model instead of here
        # avoiding NaNs
        self.hist_counts, self.hist_bins = np.histogram(
                current.twocolor[np.isfinite(current.twocolor)], bins=70)

        # equal-width bins
        dbins = (self.hist_bins[1] - self.hist_bins[0])

        for rect, h, x in zip(self.hist_patches, 
                              self.hist_counts, 
                              self.hist_bins[:-1]):
            rect.set_height(h)
            rect.set_x(x)
            rect.set_width(dbins)

        self.planck_fit_line.set_data(current.lam[current.ind_interval],
                                      current.planck_fit)

        self.planck_res_pts.set_offsets(np.c_[current.lam[current.ind_interval], 
                                              current.planck_residuals])

        if current.pars['usebg']:
            self.planck_bg.set_ydata([current.bg])
            self.rawwien_data_pts.set_offsets(np.c_[1 / current.lam, current.rawwien])

            self.planck_bg.set_visible(True)
            self.rawwien_data_pts.set_visible(True)

        else:
            self.planck_bg.set_visible(False)
            self.rawwien_data_pts.set_visible(False)

        self.wien_fit_line.set_data(1 / current.lam[current.ind_interval], 
                                    current.wien_fit)

        self.wien_res_pts.set_offsets(np.c_[1 / current.lam[current.ind_interval], 
                                            current.wien_residuals])

        self.twocolor_line.set_ydata([current.T_twocolor, current.T_twocolor])

    def set_fitslim(self, current):

        self.planck_lowlim_line.set_xdata(
                    [current.pars['lowerb'], current.pars['lowerb']])

        self.planck_highlim_line.set_xdata(
                    [current.pars['upperb'], current.pars['upperb']])

        self.wien_lowlim_line.set_xdata(
                    [1/current.pars['upperb'], 1/current.pars['upperb']])

        self.wien_highlim_line.set_xdata(
                    [1/current.pars['lowerb'], 1/current.pars['lowerb']])


    def autoscale(self, current):
        # Custom Autoscales...
        # planck:
        if current._fitted:
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
                np.nanmin( current.wien_residuals ),
                np.nanmax( current.wien_residuals )])
    
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

        else:
            # Planck:
            self.axes[0,0].set_xlim([np.min(current.lam)-100, 
                                     np.max(current.lam)+100 ])
            self.axes[0,0].set_ylim([np.min(current.planck),
                                     np.max(current.planck)])

            # Wien:
            self.axes[0,1].set_xlim(
                [np.min( 1 / current.lam - 0.0002 ),
                 np.max( 1 / current.lam + 0.0002 )])
    
            self.axes[0,1].set_ylim([np.min(current.wien),
                                     np.max(current.wien)])


class SinglePlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(
            constrained_layout=True)

        super().__init__(self.fig)



class ChooseDeltaWindow(QWidget):

    delta_changed = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent, Qt.Window)

        self.resize(400,300)

        self.setWindowTitle('Choose delta...')
        self.setStyleSheet("background-color: white")
        
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



class BatchWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent, Qt.Window)

        self.resize(800, 600)

        self.setWindowTitle('h5temperature batch')
        self.setStyleSheet("background-color: white")
        
        self.canvas = SinglePlotCanvas(self)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)     
        self.toolbar.setStyleSheet("font-size: 18px;")

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

        # click event
#        self.canvas.mpl_connect('button_press_event', self.choose)

    def replot(self, batch):
        self.canvas.ax.clear()

        self.canvas.ax.set_xlabel('Frame')
        self.canvas.ax.set_ylabel('Temperature (K)')

        self.canvas.ax.errorbar(batch.frames, batch.plancks, 
                                xerr=None,
                                yerr=batch.stddevs,
                                fmt='o',
                                capsize=2,
                                color='royalblue',
                                linestyle=None,
                                markersize=7,
                                label='Planck')

        self.canvas.ax.errorbar(batch.frames, batch.wiens,
                                xerr = None, 
                                yerr = None,
                                fmt='v',
                                capsize=3,
                                color='orange',
                                linestyle=None,
                                markersize=7,
                                label='Wien')

        self.canvas.ax.legend()

        self.canvas.ax.set_xlim([-.5, np.max(batch.frames)+.5])
        self.canvas.ax.set_ylim([np.min(batch.plancks) - 200, 
                                 np.max(batch.plancks) + 200])

        self.canvas.draw()