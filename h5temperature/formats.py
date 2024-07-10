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
import datetime

def get_data_from_h5group(group):

    t1 = str(np.array(group['end_time'])[()])
    
    try:
        time = datetime.datetime.strptime(t1, "b'%Y-%m-%dT%H:%M:%S.%f%z'")
    except:
        # fix for <python3.7, colon not supported in timezone (%z)
        if t1[-4] == ':':
            t1 = t1[:-4] + t1[-3:] # remove ":"
            time = datetime.datetime.strptime(t1, "b'%Y-%m-%dT%H:%M:%S.%f%z'")
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

def get_data_from_ascii(path):
    
    # Simplest implementation
    # This should be improved with a 'parser' for headers, separators...etc

    darr = np.loadtxt(path)
    lam = darr[:,0]
    planck = darr[:,1]

    out = dict(lam=lam, planck=planck, time=None)
    
    return out
