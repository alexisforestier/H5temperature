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

import os
import numpy as np
import datetime
import h5py
import csv

def read_h5file(path):
    with h5py.File(path, 'r') as file:
        out = dict()
        for nam, group in file.items():
            if 'measurement/T_planck' in group:
                d = get_data_from_h5group(group)
                out[nam] = d
    return out

def get_data_from_h5group(group):
    t1 = str(np.array(group['start_time'])[()])
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
    # max_data is used to check for saturation in BlackBodySpec constructor:
    max_data = np.array(group['measurement/max_data']).squeeze()

    if planck.ndim == 1:
        out = dict(lam=lam, planck=planck, max_data=max_data, time=time)
    # manage two dimensional data and return a list of dict:
    elif planck.ndim == 2:
        out = []
        for l, p, m in zip(lam, planck, max_data):
            out.append( dict(lam=l, planck=p, max_data=m, time=time) )
    else: 
        raise ValueError("Array has too many dimensions. " 
                         "Expected 1 or 2 dimensions")
    return out

def get_data_from_ascii(paths):
    out = list()
    for path in paths:
        name = path.split('/')[-1]
        darr = customparse_file2data(path)
        try:
            time = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        except:
            time = None
        lam = darr[:,0]
        planck = darr[:,1]
        # arrange data as in h5 mode:
        out.append(dict(name=name, lam=lam, planck=planck, time=time))

    return out

def customparse_file2data(f):
    with open(f, 'r') as file:
        # Skip initial lines to determine the delimiter
        initial_skip = 100  
        for _ in range(initial_skip):
            file.readline()

        # Read a chunk from the middle of the file to determine the delimiter
        chunk_size = 2000
        chunk = file.read(chunk_size)
        file.seek(0)  # Reset file pointer to the beginning

        delimiter = csv.Sniffer().sniff(chunk).delimiter

        count = 0
        data_lines = []
        # Process the file line by line to determine header
        # When it will reach footer, it will be exluded too
        for line in file:
            sp = line.strip().split(delimiter)
            if len(sp) < 2:
                count += 1
            else:
                try:
                    _ = list(map(float, sp))
                    data_lines.append(line)
                except ValueError:
                    count += 1

        #print('delimiter : {}'.format(delimiter))
        #print('count : {}'.format(count))

        # Convert data_lines to a numpy array
        data = np.array([line.strip().split(delimiter) for line in data_lines], 
            dtype=np.float64)

        #print('length: {}'.format(len(data)))
        return data[:, :2]

if __name__ == '__main__':

    path = "/home/alex/mnt/Data1/ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/hc5078_CDMX18.h5"
    path2= "/home/alex/mnt/Data1/ESRF/hc5078_10_13-02-2023-CDMX18/CDMX18/CDMX18_rampe01/CDMX18_rampe01.h5"

    from h5temperature.models import BlackBodySpec, NestedData

    test = read_h5file(path)
    alldata = NestedData()
    for k, v in test.items():
        if isinstance(v, dict):
            u = BlackBodySpec(k, **v)
            alldata[k] = u
        elif isinstance(v, list):
            thedata = NestedData()
            for i, vi in enumerate(v):
                key = f'{k}[{i}]'
                thedata[key] = BlackBodySpec(k, **vi)
            alldata[k] = thedata
    print(alldata.sort_chrono())
    print(alldata.keys())