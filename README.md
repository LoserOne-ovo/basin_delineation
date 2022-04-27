# Basin Delineation

## 1. Structure

This project provides three ways to delineate catchments based on DEM, which are organized in the following three folders:
1) The "basin" folder: river-oriented catchment delineation without considering lakes or reservoirs (i.e. the usual way in digital terrain analysis);
2) The "lake" folder: delineation of nested lake-catchments, including the delineation of full lake catchments and inter-lake catchments, the construction of topological relationship among lakes/lake-catchments, and the tracing of flow path among upstream and stream lakes. Rivers are not considered here.
2) The "lake-cat" folder: catchment delineation considering both rivers and lakes/reservoirs. The discretized units include subbasins (with one channel in each subbasin), hillslopes (without river channel and usually adjacent to lakes or reservoirs), rivers, and lakes/reservoirs. The upstream and downstream relationships among these units are constructed.

Besides, the code in the "core" folder is written in C and designed to conduct raster calculation more efficiently; The code in the "util" folder is written in Python and designed to provide general geographic data operation interfaces which are called many times. 

## 2. Dependencies

- Python >= 3.6

- GDAL >= 3.0.1

- Rtree >= 0.9.7

## 3. Data Requiremenmt

- D8 Flow Direction Data

  - datatype must be unsigned char

    - 0 - river mouth

    - 1- east

    - 2 - southeast

    - 4- south

    - 8 - southwest

    - 16 - west

    - 32 - northwest

    - 64 - north

    - 128 - northeast

    - 247 - nodata

    - 255 - inland depression