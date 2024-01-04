import numpy as np
import matplotlib.pyplot as plt
import os
import h5py
from scipy.optimize import curve_fit

h = 6.62607015e-34 # J/s
c = 299792458 # m/s
k = 1.380649 * 1e-23 # J/K


def planck(lamb, eps, temp, b):
    lambnm = lamb * 1e-9
    f = eps * ( 2*np.pi*h*c**2 / (lambnm**5) ) * 1 / ( np.exp(h * c / (lambnm * k * temp)) - 1 ) + b
    return f

def wien(I, lamb):
    lambnm = lamb * 1e-9
    f = (k / (h*c)) * np.log(2 * np.pi * h * c**2 / (I * lambnm**5) )
    return f 

def temp_2color(lamb, wien, deltapx):    
    n = np.array( [ 1/lamb[k] - 1/lamb[k + deltapx] for k in range(len(lamb)-deltapx)] )
    d = np.array( [wien[k] - wien[k + deltapx] for k in range(len(lamb)-deltapx)] )
    return(1e9 * n/d)

############################################################################
# Inputs:

# full path to h5 file:
file = h5py.File('/home/alex/mnt/Data1/ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/hc5078_CDMX18.h5', 'r')

# scan to analyze:
scan = 'CDMX18_mesh01_18.1'

# Planck fit interval in nm:
fit_interval = np.array([540, 920]) 

# delta in px for two color temperature:
deltapx = 80


############################################################################

# read data in h5 file
x = np.array( file[scan]['measurement']['spectrum_lambdas'] )
y_planck = np.array( file[scan]['measurement']['planck_data'] )
y_planck_fit = np.array( file[scan]['measurement']['planck_fit'] )


in_interval = np.array( x > fit_interval[0] ) & np.array( x < fit_interval[1] ) 
x_tofit = x[in_interval]
y_planck_tofit = y_planck[in_interval]

fig, axs = plt.subplots(2,2, figsize = (12, 9))
fig.suptitle(scan)


axs[0,0].set_xlim(fit_interval + np.array([-20, 20]))
axs[0,0].set_ylim([y_planck_tofit.min() - 0.3*y_planck_tofit.ptp(), 
                 y_planck_tofit.max() + 0.3*y_planck_tofit.ptp()] )

axs[0,0].scatter(x, y_planck, c='k', s=10, alpha=0.2, label='Planck data')

axs[0,0].plot(x, y_planck_fit, 'r--', linewidth=.8, label='old fit')

par, cov = curve_fit(planck, 
                     x_tofit, 
                     y_planck_tofit, 
                     p0     = (    1e-6,   2000,        0),
                     bounds =(( -np.inf,      0,        0),
                             (  +np.inf,    1e4,  +np.inf)),
                     method = 'trf')

axs[0,0].plot(x_tofit, planck(x_tofit, *par) , c='limegreen', linewidth=2, label='new fit')

ax_planck_res = axs[0,0].twinx()
ax_planck_res.set_ylabel('Planck fit residuals')
axs[0,0].set_zorder(1)
axs[0,0].patch.set_visible(False)

ax_planck_res.scatter(x_tofit, y_planck_tofit-planck(x_tofit, *par), 
    c='lightgray', marker='v', s=5, label='residuals')


axs[0,0].set_xlabel('wavelength (nm)')
axs[0,0].set_ylabel('intensity')

axs[0,0].text(0.4, 0.8, 'T$_\\mathrm{planck}$= ' + str( round(par[1]) ) + ' K', size=15, color='g',  transform=axs[0,0].transAxes)



print('**********************************')

print('Planck fit:')

print('epsilon    = ', par[0], '  ')
print('T planck   = ', par[1], ' K')
print('background = ', par[2], '  ')
print('**********************************\n')


# Wien fit

axs[1,0].set_xlabel('1/wavelength (1/nm)')
axs[1,0].set_ylabel('Wien')

x_wien = 1/x_tofit
y_wien = wien(y_planck_tofit, x_tofit)

axs[1,0].scatter(x_wien, y_wien, c='k', s=10, alpha=0.2, label='Wien data')

a,b = np.polyfit(x_wien, y_wien, 1)

axs[1,0].plot( x_wien, a * x_wien + b, c='limegreen', linewidth=2, label='fit')
axs[1,0]

ax_wien_res = axs[1,0].twinx()
ax_wien_res.set_ylabel('Wien fit residuals')
axs[1,0].set_zorder(1)
axs[1,0].patch.set_visible(False)

ax_wien_res.scatter( x_wien, y_wien - ( a * x_wien + b ), 
    c='lightgray', marker='v', s=5, label='residuals')

axs[1,0].text(0.3, 0.8, 'T$_\\mathrm{wien}$= ' + str( round(1e9 * 1/a) ) + ' K', size=15, color='g',  transform=axs[1,0].transAxes)



# sliding two color

temp2c = temp_2color(x_tofit, y_wien, deltapx)

axs[0,1].scatter(x_tofit[:-deltapx],  temp2c, c='k', s=5, alpha=0.2, label='two-color temperature')

axs[0,1].set_ylim([temp2c.mean()- 8*temp2c.std(), temp2c.mean()+ 8*temp2c.std()])

ax2_2c = axs[0,1].twiny()
ax2_2c.hist(temp2c, bins=int(len(temp2c)/8), orientation='horizontal', color='red', alpha=0.3, label='two-color histogram')
ax2_2c.set_xlim(np.array(ax2_2c.get_xlim()) *3)
ax2_2c.set_xlabel('frequency')

axs[0,1].axhline(y = temp2c.mean(), color='limegreen', linewidth=2, zorder=-1)
axs[0,1].text(0.3, 0.8, 'T$_\\mathrm{two-color}$ = ' + str( round(temp2c.mean()) ) + ' K', size=15, color='g',  transform=axs[0,1].transAxes)
axs[0,1].text(0.3, 0.7, 'std dev. = ' + str( round(temp2c.std()) ) + ' K', size=15, color='g',  transform=axs[0,1].transAxes)

axs[0,1].set_zorder(1)
axs[0,1].patch.set_visible(False)

axs[0,1].set_xlabel('wavelength (nm)')
axs[0,1].set_ylabel('two-color temperature (K)')

# two color T st deviation vs delta
deltas = np.array(list(range(300)))
stddevs = np.array( [ temp_2color(x_tofit, y_wien, deltas[i]).std() for i in deltas ] )

axs[1,1].scatter(deltas, stddevs, c='k', s=20, alpha=0.2, label='T$_\\mathrm{two-color}$ std dev.')
axs[1,1].axvline(x=deltapx, color='limegreen', linewidth=3)
axs[1,1].set_ylim([0, np.nanmean(stddevs)])

axs[1,1].text(deltapx+10, np.nanmean(stddevs)/2, 'current $\\delta$ = ' + str(deltapx) + ' px', size=15, color='g')
axs[1,1].set_xlabel('$\\delta$ (px)')
axs[1,1].set_ylabel('T$_\\mathrm{two-color}$ std dev. (K)')


axs[0,0].legend()
axs[1,0].legend()
axs[0,1].legend(loc = 'lower right')
axs[1,1].legend()

ax_planck_res.legend(loc='upper right')
ax_wien_res.legend(loc='upper right')
ax2_2c.legend(loc='upper right')

fig.tight_layout()
plt.show(block=True)

fig.savefig('./temp_analysis_' + scan + '.png')

file.close()

