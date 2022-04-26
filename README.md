# basin_delineation

## 1. Structure

The code of this project is split into five different parts, which are "basin", "lake", "river", "core" and "util" respectively.

- The "basin", "lake" and "river" components are written in Python and designed to delineate hydrological units at different scales.
- The "core" component is written in C and designed to finish raster calculation more efficiently. 
- The “util” component is written in Python and designed to provide general geographic data operation interfaces which are called many times in this project. 

## 2. Dependencies

Python >= 3.6

GDAL >= 3.0.1

Rtree >= 0.9.7