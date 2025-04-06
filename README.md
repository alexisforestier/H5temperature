# h5temperature

## Description

`h5temperature` is a user-friendly application designed to analyze radiometric temperature measurements from laser-heating experiments in diamond anvil cells. It supports ESRF HDF5 data files, offers data fitting with Planck and Wien formulas, and sliding two-color pyrometry analysis, as well as other features.

The analysis methods used in `h5temperature` are detailed in: [Benedetti & Loubeyre (2004), Temperature gradients,
wavelength-dependent emissivity, and accuracy of high and very-high temperatures
measured in the laser-heated diamond cell, High Pressure Research, 24:4, 423-445](https://doi.org/10.1080/08957950412331331718). 

Feel free to contribute to `h5temperature`! If you encounter any bugs or have suggestions for improvements, please report them!

## What's new (v 0.4.1)

* A batch fit feature is available, allowing you to fit all data from a group (e.g., temperature ramp) or all data loaded in `h5temperature` at once
* An `autofit` mode can be activated or deactivated. When activated, clicking a measurement item in the list will automatically fit the data. If deactivated, data can be fitted by clicking the fit button. This is useful for setting different fit parameters for different measurements
* All fit results from the session can be exported in ASCII format
* Saturated spectra are detected, and spectral regions where saturation occurs are indicated with a red square in the Planck plot
* ASCII data can be loaded for analysis (currently, only one file can be loaded at a time)
* The fit range is now indicated with vertical green lines
* The code has been refactored into a Python package.
* A few bug fixes
* A new icon ! :)

## Requirements 

Python3 packages:

* h5py
* numpy
* matplotlib
* scipy
* pyqt5

## Running the Program

### From source 

#### Using poetry

The easiest way is using poetry. Clone the repository and navigate to the `H5temperature` directory:
```
git clone https://github.com/alexisforestier/H5temperature.git
cd H5temperature
```

Then run from the `H5temperature` directory:
```
poetry install
```
To activate the newly created environment run:
```
poetry shell
```
Then `h5temperature` can be started, type:
```
h5temperature
```

#### Another way

Ensure you have the requirements listed above installed. To install all required dependencies at once, run in the `H5temperature` directory:
```
pip install -r requirements.txt
```
Then the following command will start the program: 
```
python3 run.py
```
or run the `run.py` file from any python interpreter.

### Executable for Windows 

__Download the latest Release for Windows ([here](https://github.com/alexisforestier/H5temperature/releases)), unpack it, and run *h5temperature.exe.*__ 
Tested on Windows 10 only

> [!NOTE]  
>In case of errors occurring at launch, particularly regarding module imports, it may be necessary to install Microsoft Visual C++ Redistributable. You can find it here: [https://learn.microsoft.com/fr-fr/cpp/windows/latest-supported-vc-redist?view=msvc-170](https://learn.microsoft.com/fr-fr/cpp/windows/latest-supported-vc-redist?view=msvc-170).


## Use 

Use the "Load h5" button to load a specific HDF5 file. 
All temperature measurements within this file will be displayed.

The fit is performed automatically when you click on a measurement in the left panel, if the `autofit` mode is active. Otherwise, click the "Fit" button. 

## Future improvements

* Use PyQtGraph instead of matplotlib for better performance
* Save and load work sessions
* Batch loading of several files in ASCII format
* 2D representation of the fitted batch for temperature mapping