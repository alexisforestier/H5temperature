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

        super(FourPlotsCanvas, self).__init__(self.fig)

    def get_NavigationToolbar(self, parent):
        return NavigationToolbar2QT(self, parent)

class SinglePlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(
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
        self.toolbar.setStyleSheet("font-size: 18px;")

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.setLayout(layout)