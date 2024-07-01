# h5temperature

## Description

`h5temperature` is a user-friendly application designed for analyzing radiometric temperature measurements from laser-heating experiments in diamond anvil cells. __It supports ESRF HDF5 data files__, offers data fitting with Planck and Wien formulas, and sliding two-color pyrometry analysis. 

The methods used in `h5temperature` are detailed in: [Benedetti & Loubeyre (2004), Temperature gradients,
wavelength-dependent emissivity, and accuracy of high and very-high temperatures
measured in the laser-heated diamond cell, High Pressure Research, 24:4, 423-445](https://doi.org/10.1080/08957950412331331718). 

## Requirements 

Python3 packages:

* h5py
* numpy
* matplotlib
* scipy
* pyqt5

## Running the Program

### From source 

__Check you have the requirements above installed for your python3 distribution. Then run__

```
python3 run.py
```
or run it through any python interpreter.

To install all required dependencies, run in the H5temperature directory:
```
pip install -r requirements.txt
```

### Executable for Windows 

__Download the latest Release for Windows ([here](https://github.com/alexisforestier/H5temperature/releases)), unpack it, and run *h5temperature.exe.*__ 
Tested on Windows 10 only

> [!NOTE]  
>In case of errors occurring at launch, particularly regarding module imports, it may be necessary to install Microsoft Visual C++ Redistributable. You can find it here: [https://learn.microsoft.com/fr-fr/cpp/windows/latest-supported-vc-redist?view=msvc-170](https://learn.microsoft.com/fr-fr/cpp/windows/latest-supported-vc-redist?view=msvc-170).


## Use 

Use the "Load h5" button to load a specific HDF5 file. **Currently, one must open the .h5 file corresponding to a *newsample('Samplename')* created from BLISS, typically named *Proposalname_Samplename.h5*.** 
All temperature measurements within this file will be displayed.

The fit is performed automatically upon clicking on a measurement in the left panel. If you make changes to the parameters, click "Fit" to apply them. 

## Future improvements

* Save and load sessions.
* Export an ASCII results table, for the whole session?
* Recursively locate temperature data from any HDF5 file in the arborescence? Tried but long!
* Ability to load txt files from other sources than ESRF h5 data.
