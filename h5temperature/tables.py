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

from PyQt5.QtWidgets import (QTableWidget,
                            QTableWidgetItem,
                            QAbstractItemView,
                            QHeaderView,
                            QSizePolicy)


class SingleFitResultsTable(QTableWidget):
    def __init__(self):
        super().__init__(6,1)

        self.setStyleSheet('QTableWidget '
                           '{border: 1px solid gray ;'
                            'font-weight: bold ;'
                            'background-color: white ;}')

        self.resizeRowsToContents()
        self.resizeColumnsToContents()
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        # not selectable, not editable:
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.setVerticalHeaderLabels(["T Planck (K)", 
                                      "T Wien (K)",
                                      "T 2-color (K)",
                                      "T 2-c std dev (K)",
                                      "multiplier Planck",
                                      "multiplier Wien"])

    def set_values(self, current):
        self.setItem(0, 0, QTableWidgetItem(str(round(current.T_planck))))
        self.setItem(0, 1, QTableWidgetItem(str(round(current.T_wien))))
        self.setItem(0, 2, QTableWidgetItem(str(round(current.T_twocolor))))
        self.setItem(0, 3, QTableWidgetItem(str(round(current.T_std_twocolor))))
        self.setItem(0, 4, QTableWidgetItem(str(round(current.eps_planck,3))))
        self.setItem(0, 5, QTableWidgetItem(str(round(current.eps_wien,3))))