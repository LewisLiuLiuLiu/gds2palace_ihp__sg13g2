# Change list 

This is an (incomplete) list of changes and new features.

## 9-Dec-2025
Fixed an issue that caused mesh error when stacked objects overlapped exactly. Now, stacking objects with same size (resulting in shared surface) works correct.

A Python-based user interface for gds2palace named setupEM is now available. 
You can install this using pip install:

```
    pip install setupEM
```
This is work in progress with frequent updates, which can be installed using
```
    pip install setupEM --upgrade
```

Project source and documentation: 
https://github.com/VolkerMuehlhaus/setupEM

## 10-Jan-2025
Fixed bug in port metadata information for in-plane ports, direction was not properly evaluated in some cases (check for "X" orientation was case sensitive). This resulted in incorrect port de-embedding, with width and length swapped for in-plane ports specified as "x" or "-x" direction. 

## 1-Dec-2025
Instead of always having the gds2palace directory in your working directory, 
you can also install gds2palace module to your venv using pip install:

```
    pip install gds2palace
```

https://pypi.org/project/gds2palace/

## 23-Nov-2025
- Added optional setting: options["fdump"] = [frequency] to create Palace points list with field dump enabled. 
- New example file palace_butlermatrix_dump93.py shows usage of fdump option. 

- Updated User's guide with new options, added a chapter listing examples

## 22-Nov-2025
- Added optional setting: options["fpoint"] = [frequency] to specify single frequency or list [] of frequencies separated by comma

## 21-Nov-2025
- Calculation of maximum meshsize is now per dielectric layer, means larger mesh cells in air and oxide.
- Added check to enforce gdspy version 1.6 or later, because gdspy 1.4.2 causes issues.
- Add version information for gds2python module files.
- Palace solver setting changed to AdaptiveTol = 2e-2

## 19-Nov-2025
- Improved combine_extend_snp code (postprecessing of results Palace to SnP) to handle more than 9 ports
