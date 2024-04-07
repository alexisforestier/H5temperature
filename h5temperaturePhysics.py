import numpy as np

h = 6.62607015e-34 # Planck's constant in J/s
c = 299792458 # Speed of light in m/s
k = 1.380649 * 1e-23 # Boltzmann constant in J/K

# all function takes lamb in nm
def planck(lamb, eps, temp, bg = 0):
    lamb = lamb * 1e-9 # now in meters
    f =  ( eps * ( 2*np.pi*h*c**2 / (lamb**5) ) * 
         1 / ( np.exp(h * c / (lamb * k * temp)) - 1 ) ) + bg 
    return f

def wien(lamb, I, bg = 0):
    lamb = lamb * 1e-9 # now in meters

    I2 = (I-bg)
    # SHOULD BE IMPROVED?
    I2[I2<0] = 1e-8

    f = (k / (h*c)) * np.log(2 * np.pi * h * c**2 / (I2 * lamb**5) )
    return f

def temp2color(lamb, wien, deltapx):    
    n = np.array( [ 1/lamb[k] - 1/lamb[k + deltapx]
                    for k in range(len(lamb)-deltapx)] )
    d = np.array( [wien[k] - wien[k + deltapx]
                    for k in range(len(lamb)-deltapx)] )
    return(1e9 * n/d)