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
import datetime
from scipy.optimize import curve_fit
from copy import deepcopy
#import time

import h5temperaturePhysics as Ph


def get_data_from_h5group(group):

    t1 = str(np.array(group['end_time'])[()])
    
    try:
        time = datetime.datetime.strptime(t1, 
                    "b'%Y-%m-%dT%H:%M:%S.%f%z'")
    except:
        # fix for <python3.7, colon not supported in timezone (%z)
        if t1[-4] == ':':
            t1 = t1[:-4] + t1[-3:] # remove ":"
            self.time = datetime.datetime.strptime(t1, 
                        "b'%Y-%m-%dT%H:%M:%S.%f%z'")
        else:
            time = None

    lam = np.array(group['measurement/spectrum_lambdas']).squeeze()
    planck = np.array(group['measurement/planck_data']).squeeze()

    if planck.ndim == 1:
        out = dict(lam=lam, planck=planck, time=time)
    # manage two dimensional data and return a list of dict:
    elif planck.ndim == 2:
        out = []
        for l,p in zip(lam, planck):
            out.append( dict(lam=l, planck=p, time=time) )
    else: 
        raise ValueError("Array has too many dimensions. " 
                         "Expected 1 or 2 dimensions")
    return out





class BlackBodySpec():
    def __init__(self, name, lam, planck, time=None):

        # reordering...
        ordind = np.argsort(lam)
        self.lam = lam[ordind]
        self.planck = planck[ordind]
        
        self.name = name 
        self.time = time
        
        if self.time:
            self.timestamp = self.time.timestamp()
        else:
            self.timestamp = None


        self.rawwien = Ph.wien(self.lam, self.planck)
        # wien initialized as rawwien:
        self.wien = self.rawwien

        # pars for a given measurement.
        self.pars = dict(lowerb = None,
                         upperb = None,
                         delta  = None,
                         usebg  = None)

        self.ind_interval = None
        self.bg = 0

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
        # deepcopy necessary otherwise always point to the mainwindow pars!
        self.pars = deepcopy(pars)
        self.ind_interval = np.logical_and(self.lam >= self.pars['lowerb'], 
                                           self.lam <= self.pars['upperb'])

    def eval_twocolor(self):
        # calculate 2color 
        self.twocolor = Ph.temp2color(
                        self.lam[self.ind_interval], 
                        self.wien[self.ind_interval], 
                        self.pars['delta'])
        # namean/std for cases where I-bg < 0
        self.T_twocolor = np.nanmean(self.twocolor)
        self.T_std_twocolor = np.nanstd(self.twocolor)
        

    def eval_wien_fit(self):
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
        # initial temperature value for the fit...
        if self.T_wien:
            Tguess = self.T_wien
        else:
            Tguess = 2000

        # initial values:
        if self.pars['usebg']:
                       # eps,   temp,      bg
            p0      =  (1e-6,  Tguess,        0)
            pbounds = ((   0,       0,  -np.inf),
                       (   1,     5e4,  +np.inf))
        else:
                       # eps,   temp
            p0      =  (1e-6,   Tguess)
            pbounds = ((   0,        0),
                       (   1,      5e4))

        p_planck, cov_planck = curve_fit(Ph.planck, 
                                         self.lam[self.ind_interval], 
                                         self.planck[self.ind_interval],                         
                                         p0 = p0,
                                         bounds = pbounds)    

        self.planck_fit = Ph.planck(self.lam[self.ind_interval], *p_planck)
        self.planck_residuals = self.planck[self.ind_interval]-self.planck_fit
        self.T_planck = p_planck[1]
        self.eps_planck = p_planck[0]

        if self.pars['usebg']:
            self.bg = p_planck[-1]
            self.wien = Ph.wien(self.lam, self.planck, self.bg)

        else:
            # if desactivated, bg is set back to 0
            self.bg = 0
            # and original wien is recovered
            self.wien = self.rawwien



if __name__ == '__main__':
    
    import matplotlib.pyplot as plt 

    #with h5py.File('/home/alex/mnt/Data1/' 
    #    'ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/hc5078_CDMX18.h5', 'r') as file:
#
    #    g = file['CDMX18_rampe01_14.1']
    #    print(g)
#
    #    data = get_data_from_h5group(g)
    #    print(data)
#
    #    test = BlackBodySpec('test', **data)
    #    test.set_pars(dict(usebg=None, delta=113, lowerb=570, upperb = 920))
#
    #    print(test.time)
#
    #    test.eval_twocolor()
    #    test.eval_planck_fit()
    #    test.eval_wien_fit()
#
    #    plt.figure(1)
    #    plt.plot(test.lam, test.planck)
    #    plt.plot(test.lam[test.ind_interval], test.planck_fit)
    #    
    #    plt.figure(2)
    #    plt.plot(1/test.lam, test.wien)
    #    plt.plot(1/test.lam[test.ind_interval], test.wien_fit)
    #    
    #    plt.figure(3)
    #    plt.plot(test.lam[test.ind_interval][:-test.pars['delta']], test.twocolor)
#
    #    print(test.T_planck)
    #    print(test.T_wien)
    #    print(test.T_twocolor)
    #    print(test.T_std_twocolor)
#
    #    plt.show()
    with h5py.File('/home/alex/mnt/Data1/' 
        'ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/hc5078_CDMX18.h5', 'r') as file:
        g = file['CDMX18_mesh_HT_1.1']
        print(g)

        data = get_data_from_h5group(g)
        print(data[3])