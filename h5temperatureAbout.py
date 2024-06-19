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


from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

__version__ = '0.3'


class AboutWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.resize(420, 300)
        self.setWindowTitle('About h5temperature')
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout()

        title = QLabel('h5temperature {}'.format(__version__))
        title.setStyleSheet("font-weight: bold;"
                            "font-size: 22pt")

        text1 = QLabel('Analysis methods used in h5temperature' 
                    ' are detailed in: '
                    '<a href=\"https://doi.org/10.1080/08957950412331331718\">'
                    'Benedetti and Loubeyre (2004), '
                    'High Pressure Research, 24:4, 423-445</a>')

        text1.setOpenExternalLinks(True)

        text2 = QLabel('Copyright 2023-2024 Alexis Forestier '
                       '(alforestier@gmail.com)')

        text3 = QLabel('h5temperature is free software: you can redistribute '
                        'it and/or modify it under the terms of the ' 
                        'GNU General Public License as published by the '
                       'Free Software Foundation, either version 3 of the ' 
                       'License, or (at your option) any later version. '
                       'h5temperature is distributed in the hope that it ' 
                       'will be useful, but WITHOUT ANY WARRANTY; without ' 
                       'even the implied warranty of MERCHANTABILITY or '
                       'FITNESS FOR A PARTICULAR PURPOSE. See the GNU '
                       'General Public License for more details. '
                       'You should have received a copy of the GNU General '
                       'Public License along with h5temperature. ' 
                       'If not, see <a href=\"https://www.gnu.org/licenses/\">'
                       'https://www.gnu.org/licenses/</a>.')

        text3.setStyleSheet("font-style: italic;"
                            "font-size: 8pt")

        text3.setOpenExternalLinks(True)

        title.setAlignment(Qt.AlignCenter)
        text1.setAlignment(Qt.AlignCenter)
        text2.setAlignment(Qt.AlignCenter)
        text3.setAlignment(Qt.AlignCenter)

        title.setWordWrap(True)
        text1.setWordWrap(True)
        text2.setWordWrap(True)
        text3.setWordWrap(True)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(text1)
        layout.addStretch()
        layout.addWidget(text2)
        layout.addStretch()
        layout.addWidget(text3)

        self.setLayout(layout)