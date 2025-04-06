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
import h5py
import datetime
from scipy.optimize import curve_fit
from copy import deepcopy

import h5temperature.physics as Ph


class BlackBodySpec():
    def __init__(self, name, lam, planck, max_data=None, time=None):

        # reordering...
        ordind = np.argsort(lam)
        self.lam = lam[ordind]
        self.planck = planck[ordind]
        max_data = max_data[ordind]
        
        self.name = name
        self.time = time
        
        if self.time:
            self.timestamp = self.time.timestamp()
        else:
            self.timestamp = None

        self.rawwien = Ph.wien(self.lam, self.planck)
        
        # wien initialized as rawwien:
        # rawwien will remain the same 
        self.wien = self.rawwien

        # pars for a given measurement.
        self.pars = dict(lowerb = None,
                         upperb = None,
                         delta  = None,
                         usebg  = None)

        # fitted flag 
        self._fitted = False

        # check for saturation:
        if max_data is not None:
            self.saturated_ind = np.where(max_data >= (2**16 - 1))[0]
            self._saturated = (len(self.saturated_ind) > 0)
        else:
            # absence of raw data to check
            self.saturated_ind = np.array([])
            self._saturated = False

        self.bg = 0
        self.ind_interval = None

        self.twocolor = None
        self.T_twocolor = None
        self.T_std_twocolor = None

        self.wien_fit = None
        self.wien_residuals = None
        self.T_wien = None
        self.eps_wien = None

        self.planck_fit = None
        self.planck_residuals = None
        self.T_planck = None
        self.eps_planck = None


    def set_pars(self, pars):
        # deepcopy necessary otherwise always point to the mainwindow pars!!
        self.pars = deepcopy(pars)
        self.ind_interval = np.logical_and(self.lam >= self.pars['lowerb'], 
                                           self.lam <= self.pars['upperb'])

    def eval_twocolor(self):

        if not self._fitted:
            self._fitted = True

        # calculate 2color 
        self.twocolor = Ph.temp2color(self.lam[self.ind_interval], 
                                      self.wien[self.ind_interval], 
                                      self.pars['delta'])

        # namean/std for cases where I-bg < 0, it returns nan
        self.T_twocolor = np.nanmean(self.twocolor)
        self.T_std_twocolor = np.nanstd(self.twocolor)
        

    def eval_wien_fit(self):

        if not self._fitted:
            self._fitted = True

        # in cases of I-bg < 0, the wien fct returns np.nan:
        # we keep only valid data for the fit.
        keepind = np.isfinite(self.wien[self.ind_interval])
        
        x1 = (1/self.lam[self.ind_interval])[keepind]
        y1 = (self.wien[self.ind_interval])[keepind]

        a, b = np.polyfit(x1, y1, 1) # order = 1, linear
        
        self.wien_fit = a / self.lam[self.ind_interval] + b
        self.wien_residuals = self.wien[self.ind_interval] - self.wien_fit

        self.T_wien = 1e9 * 1/a # in K ; as wien fonction use lam in m
        # no factor required for b:
        self.eps_wien = np.exp(- b * Ph.h * Ph.c / Ph.k)
       

    def eval_planck_fit(self):

        if not self._fitted:
            self._fitted = True

        # initial temperature value for the fit...
        if self.T_wien:
            Tguess = self.T_wien
            eps_guess = self.eps_wien
        else:
            Tguess = 2000
            eps_guess = 1e-6

        if self.pars['usebg']:
                       # eps     ,   temp ,        bg
            p0      =  (eps_guess,   Tguess,        0)
            pbounds = ((        0,        0,        0),
                       (  +np.inf,      2e4,  +np.inf))
        else:
                       # eps     ,   temp     
            p0      =  (eps_guess,   Tguess)
            pbounds = ((        0,        0),
                       (  +np.inf,      2e4))

        p_planck, cov_planck = curve_fit(Ph.planck, 
                                         self.lam[self.ind_interval], 
                                         self.planck[self.ind_interval],                         
                                         p0 = p0,
                                         bounds = pbounds,
                                         method = 'dogbox')    

        self.planck_fit = Ph.planck(self.lam[self.ind_interval], *p_planck)
        self.planck_residuals = self.planck[self.ind_interval]-self.planck_fit
        self.T_planck = p_planck[1]
        self.eps_planck = p_planck[0]

        if self.pars['usebg']:
            self.bg = p_planck[2]
            self.wien = Ph.wien(self.lam, self.planck, self.bg)
        else:
            self.bg = 0
            self.wien = self.rawwien


class TemperaturesBatch():
    def __init__(self, measurements):
        # measurements is now a simple list.
        self.measurements = measurements
        self.n_points = len(self.measurements)

        self.keys = [0 for _ in range(self.n_points)]

        self.frames = np.empty(self.n_points)
        self.plancks = np.empty(self.n_points)
        self.wiens = np.empty(self.n_points)
        self.stddevs = np.empty(self.n_points)

        self.extract_all()

    # as batch fit calls the constructor it will reinitiate 
    # self.keys and everything else
    # otherwise if extract all is called, I have to overwrite self.keys()
    # but the length remains the same. Hence I do not use append.
    def extract_all(self):
        # populate everything
        for i, meas in enumerate(self.measurements):
            # keys is a list
            self.keys[i] = meas.name

            # np.arrays
            self.frames[i] = i
            self.plancks[i] = meas.T_planck
            self.wiens[i] = meas.T_wien
            self.stddevs[i] = meas.T_std_twocolor