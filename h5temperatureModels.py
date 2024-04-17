import numpy as np 
import h5py
import datetime
from scipy.optimize import curve_fit
from copy import deepcopy

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
        # calculate 2color 
        self.twocolor = Ph.temp2color(
                        self.lam[self._ininterval], 
                        self.wien[self._ininterval], 
                        self.pars['delta'])

        self.T_twocolor = np.mean(self.twocolor)
        self.T_std_twocolor = np.std(self.twocolor)

    def eval_wien_fit(self):

        a, b = np.polyfit(1/self.lam[self._ininterval], 
                          self.wien[self._ininterval], 
                          1) # order = 1, linear
        
        self.wien_fit = a / self.lam[self._ininterval] + b
        self.wien_residuals = self.wien[self._ininterval] - self.wien_fit

        self.T_wien = 1e9 * 1/a # in K ; as wien fonction use lam in m
        # no factor required for b:
        self.eps_wien = np.exp(- b * Ph.h * Ph.c / Ph.k)

    def eval_planck_fit(self):
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
            p0      =  (1e-6, Tguess,       0)
            pbounds = ((   0,      0, -np.inf),
                       (   1,    1e5, +np.inf))
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
            self.wien = self.rawwien

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