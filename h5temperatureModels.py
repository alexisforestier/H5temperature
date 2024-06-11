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
import time

import h5temperaturePhysics as Ph

class BlackBodyFromh5():
    def __init__(self, group, name):

        self.name = name
        t1 = str(np.array(group['end_time'])[()])

        try:
            self.time = datetime.datetime.strptime(t1, 
                        "b'%Y-%m-%dT%H:%M:%S.%f%z'")
            self.timestamp = self.time.timestamp()

        except:
            # fix for <python3.7, colon not supported in timezone (%z)
            if t1[-4] == ':':
                t1 = t1[:-4] + t1[-3:] # remove ":"
                self.time = datetime.datetime.strptime(t1, 
                            "b'%Y-%m-%dT%H:%M:%S.%f%z'")
                self.timestamp = self.time.timestamp()
            else:
                pass

        lam1 = np.array(group['measurement/spectrum_lambdas'])
        # reordering...
        ordind = np.argsort(lam1)

        if lam1.ndim == 1:  # normal case
            self.lam = lam1[ordind]
            self.planck = np.array(group['measurement/planck_data'])[ordind]

        # Rare case of a mesh of T measurements -> Unsupported.
        # no ordering to avoid errors due to indexing with ordind. 
        else: 
            self.lam = lam1
            self.planck = np.array(group['measurement/planck_data'])

        self.rawwien = Ph.wien(self.lam, self.planck)
        # wien initialized as rawwien:
        self.wien = self.rawwien

        self.pars = dict(lowerb = None,
                         upperb = None,
                         delta  = None,
                         usebg  = None)


        self._ininterval = None
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
        self._ininterval = np.logical_and(self.lam >= self.pars['lowerb'], 
                                          self.lam <= self.pars['upperb'])

    def eval_twocolor(self):
        start = time.time()
        # calculate 2color 
        self.twocolor = Ph.temp2color(
                        self.lam[self._ininterval], 
                        self.wien[self._ininterval], 
                        self.pars['delta'])
        # nan for cases where I-bg < 0
        self.T_twocolor = np.nanmean(self.twocolor)
        self.T_std_twocolor = np.nanstd(self.twocolor)
        
        end = time.time()
        print('time in eval_twocolor = ', end-start)

    def eval_wien_fit(self):
        start = time.time()
        # in cases of I-bg < 0, the wien fct returns np.nan:
        keepind = np.isfinite(self.wien[self._ininterval])
        x1 = (1/self.lam[self._ininterval])[keepind]
        y1 = (self.wien[self._ininterval])[keepind]

        a, b = np.polyfit(x1, y1, 1) # order = 1, linear
        
        self.wien_fit = a / self.lam[self._ininterval] + b
        self.wien_residuals = self.wien[self._ininterval] - self.wien_fit

        self.T_wien = 1e9 * 1/a # in K ; as wien fonction use lam in m
        # no factor required for b:
        self.eps_wien = np.exp(- b * Ph.h * Ph.c / Ph.k)
        end = time.time()
        print('time in eval_wien_fit = ', end-start)        

    def eval_planck_fit(self):
        start = time.time()
        # lead to some problem with oscillating Tguess 
        # hence oscillating solution:
        #
        #if self.T_wien:
        #    Tguess = self.T_wien
        #else:
        #    Tguess = 2000

        Tguess=2000
        # initial values:
        if self.pars['usebg']:
                       # eps,   temp,      bg
            p0      =  (1e-6, Tguess,        0)
            pbounds = ((   0,      0,  -np.inf),
                       (   1,    1e5,  +np.inf))
        else:
                       # eps,   temp
            p0      =  (1e-6, Tguess)
            pbounds = ((   0,      0),
                       (   1,    1e5))

        #print(p0)
        p_planck, cov_planck = curve_fit(Ph.planck, 
                                         self.lam[self._ininterval], 
                                         self.planck[self._ininterval],                         
                                         p0 = p0,
                                         bounds = pbounds)    

        self.planck_fit = Ph.planck(self.lam[self._ininterval], *p_planck)
        self.planck_residuals = self.planck[self._ininterval] - self.planck_fit
        self.T_planck = p_planck[1]
        self.eps_planck = p_planck[0]

        if self.pars['usebg']:
            self.bg = p_planck[-1]
            self.wien = Ph.wien(self.lam, self.planck, self.bg)

        else:
            # if desactivated, bg is set back to 0
            self.bg = 0
            # original wien is recovered
            self.wien = self.rawwien

        end = time.time()
        print('time in eval_planck_fit = ', end-start) 

if __name__ == '__main__':

    with h5py.File('/home/alex/mnt/Data1/ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/hc5078_CDMX18.h5', 'r') as file:
      #  print(file['CDMX18_rampe01_14.1/measurement'].keys())
        lam = np.array(file['CDMX18_rampe01_14.1/measurement/spectrum_lambdas'])
        planck = np.array(file['CDMX18_rampe01_14.1/measurement/planck_data'])
        

        test = BlackBodyFromh5(file['CDMX18_rampe01_14.1'], 'test1')
        
        print( test.lam[40] )
        print( test.lam[40+50] )

        print( np.argsort(test.lam) )

#        data = np.column_stack((lam, planck))
#        print(data)

        #import matplotlib.pyplot as plt
        #plt.plot(data[:,0], data[:,1])
        #plt.show()

        #np.savetxt('test.csv', data, delimiter = '\t')
        #x = np.loadtxt('test.csv', delimiter = '\t')
        #plt.plot(x[:,0], x[:,1])
        #plt.show()