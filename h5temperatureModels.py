import numpy as np 
import h5py
import datetime
from scipy.optimize import curve_fit

import h5temperaturePhysics

class BlackBodyFromh5():
    def __init__(self, group, name):

        self.name = name
        t1 = str(np.array(group['end_time'])[()])
        self.time = datetime.datetime.strptime(t1, 
                        "b'%Y-%m-%dT%H:%M:%S.%f%z'")
        self.timestamp = self.time.timestamp()

        self.lam = np.array(group['measurement/spectrum_lambdas'])
        self.planck = np.array(group['measurement/planck_data'])

        self.wien = h5temperaturePhysics.wien(self.lam, self.planck)

        self.twocolor = None
        self.T_std_twocolor = None

        self.wien_fit = None
        self.wien_residuals = None
        self.T_wien = None

        self.planck_fit = None
        self.planck_residuals = None
        self.T_planck = None

    def lam_infit(self, interval):
        within = np.logical_and(self.lam >= interval[0], 
                                self.lam <= interval[1])
        return self.lam[within]

    def eval_twocolor(self, interval, delta):
        # interval as a tuple (min, max)
        within = np.logical_and(self.lam >= interval[0], 
                                self.lam <= interval[1])
        # calculate 2color 
        self.twocolor = h5temperaturePhysics.temp2color(
                        self.lam[within], 
                        self.wien[within], 
                        delta)

        self.T_twocolor = np.mean(self.twocolor)
        self.T_std_twocolor = np.std(self.twocolor)

    def eval_wien_fit(self, interval):
        # interval as a tuple (min, max)
        within = np.logical_and(self.lam >= interval[0], 
                                self.lam <= interval[1])

        a, b = np.polyfit(1/self.lam[within], 
                          self.wien[within], 
                          1) # order = 1, linear
        
        self.wien_fit = a/self.lam[within] + b
        self.wien_residuals = self.wien[within] - self.wien_fit
        self.T_wien = 1e9 * 1/a # in K

    def eval_planck_fit(self, interval):
        # interval as a tuple (min, max)
        within = np.logical_and(self.lam >= interval[0], 
                                self.lam <= interval[1])

        if self.T_wien:
            Tguess = self.T_wien
        else:
            Tguess = 2000

        p_planck, cov_planck = curve_fit(h5temperaturePhysics.planck, 
                                         self.lam[within], 
                                         self.planck[within], 
                                                 # eps,   temp
                                    p0     = (    1e-6,  Tguess),
                                    bounds =(( -np.inf,       0),
                                            (  +np.inf,     1e5)))    

        self.planck_fit = h5temperaturePhysics.planck(self.lam[within], 
                                                        *p_planck)
        self.planck_residuals = self.planck[within] - self.planck_fit
        self.T_planck = p_planck[1]


if __name__ == '__main__':

    i = 0 
    with h5py.File('/media/alex/Data1/ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/hc5078_CDMX18.h5', 'r') as file:
        for k, v in file.items():
            if 'measurement/T_planck' in v:
                i+=1
    print(i)
