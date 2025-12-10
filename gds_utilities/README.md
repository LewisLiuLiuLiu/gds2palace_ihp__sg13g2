These Python scripts are specifically designed for IHP SG13G2 technology and might help in preprocessing GDSII layouts for EM simulation

## gds_simplify 
This script performs two functions:
- remove inner square cutout from polygons, as used to fulfill density rules
- detect circle-like shapes and replace them by octagon shapes

These functions will lead to less mesh complexity in FEM smulations.

Run this script from the venv where you also run gds2palace, because it requires the gdspy module. The output file will be created in the same directory as the input file, with file suffix "_forEM.gds"

```
source ~/venv/palace/bin/activate
python gds_simplify.py inputfile.gds
```

Example input file with square holes in the center:

<img src="../doc/png/cutout1.png" alt="cutout" width="700">

Result after running gds_simplify:

<img src="../doc/png/cutout2.png" alt="cutout" width="700">


## gds_viamerge
This script performs via array simplification for layouts in in IHP SG13G2 technology. 

It is more powerful than the via array merging built into gds2palace, because it can handle large spacings betweem vias that occur under pads, for exemple. The avoid creating brdiges (shorts) between closely spaced polygons, gds_viamerge clips the merged via arrays to the metal layers above and below. This cuts false brigdes that might be created by via array merging.

Run this script from the venv where you also run gds2palace, because it requires the gdspy module. The output file will be created in the same directory as the input file, with file suffix "_viamerge.gds"

```
source ~/venv/palace/bin/activate
python gds_viamerge.py inputfile.gds
```

Example input file with via array under pad (shown: TopVia1, TopVia2, TopMetal2):

<img src="../doc/png/viaarray1.png" alt="vias" width="700">

Result after running gds_viamerge:

<img src="../doc/png/viaarray2.png" alt="vias" width="700">

The vias are merged into larger polygons, but for TopVia1 the resulting shape is two pieces instead of one circle. This depends on the values used for array merging (oversize value) and can be fixed by manual merging in klayout.

**When the via arrays under the pads are merged into one circle-like polygon shape, we could run gds_simplify again to detect this and create a clean octagon shape instead of the circle-like polygon with hundreds of edges. The large amount of edges would result in a complex dense mesh, the octagon is much nicer for FEM meshing.**



