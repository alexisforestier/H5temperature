import numpy as np 
#import pandas as pd
import h5py
import datetime
from scipy.optimize import curve_fit

import os
os.chdir('/home/alex/python/h5temperature')

import h5temperaturePhysics

class BlackBodyFromh5():
    def __init__(self, group):

        t1 = str(np.array(group['end_time'])[()])
        self.time = datetime.datetime.strptime(t1, 
                        "b'%Y-%m-%dT%H:%M:%S.%f%z'")
        self.timestamp = self.time.timestamp()

        self.lam = np.array(group['measurement/spectrum_lambdas'])
        self.planck = np.array(group['measurement/planck_data'])
        
        self.invlam = 1/self.lam
        self.wien = h5temperaturePhysics.wien(self.lam, self.planck)

    def twocolor(self, interval, delta):
        # interval as a tuple (min, max)
        within = np.logical_and(self.lam >= interval[0], 
                                self.lam <= interval[1])
        # calculate 2color 
        y_2c = h5temperaturePhysics.temp2color(self.lam[within], 
                          self.wien[within], 
                          delta)
        return y_2c

    def wien_fit(self, interval):
        # interval as a tuple (min, max)    
        within = np.logical_and(self.lam >= interval[0], 
                                self.lam <= interval[1])

        a, b = np.polyfit(1/self.lam[within], self.wien[within], 1)
        
        x = self.invlam[within]
        y = a/self.lam[within] + b
        r = self.wien[within] - y
        T = 1e9 * 1/a # in K

        return x, y, r, T

    def planck_fit(self, interval):
        within = np.logical_and(self.lam >= interval[0], 
                                self.lam <= interval[1])

        Tguess = self.wien_fit(interval)[3]

        p_planck, cov_planck = curve_fit(h5temperaturePhysics.planck, 
                                         self.lam[within], 
                                         self.planck[within], 
                                    p0     = (    1e-6,  Tguess,        0),
                                    bounds =(( -np.inf,       0,        0),
                                            (  +np.inf,     1e5,  +np.inf)))    
        x = self.lam[within]
        y = h5temperaturePhysics.planck(x, *p_planck)
        r = self.planck[within] - y
        T = p_planck[1]
        
        return x, y, r, T

#if __name__ == '__main__':

path= '/media/alex/Data1/ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/hc5078_CDMX18.h5'
    
with h5py.File(path, 'r') as f: 
    a = f['CDMX18_mesh01_18.1']


test = BlackBodyFromh5(a)

import matplotlib.pyplot as plt


plt.plot(test.lam, test.planck)
plt.plot(test.planck_fit( (600, 900) )[0], test.planck_fit( (600, 900) )[1]) 
plt.show()