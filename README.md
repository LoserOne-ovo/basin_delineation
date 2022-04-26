# Basin Delineation

## 1. Structure

The code of this project is split into five different parts, which are "basin", "lake", "river", "core" and "util" respectively.

- The "basin", "lake" and "river" components are written in Python and designed to delineate hydrological units at different scales.
- The "core" component is written in C and designed to finish raster calculation more efficiently. 
- The “util” component is written in Python and designed to provide general geographic data operation interfaces which are called many times in this project. 

## 2. Dependencies

- Python >= 3.6

- GDAL >= 3.0.1

- Rtree >= 0.9.7

## 3. Data Requiremenmt

- D8 Flow Direction Data (MERTI Hydro, reference: http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/index.html)

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

## 4. Algorithm

- Reversed D8 Flow Direction

  To help track upslope pixels more efficiently, a reversed D8 flow direction array is calculated. If a pixel has value 69 (10000101), it means the east, south, northeast neighbor pixels are upslope pixels of the center pixel.

- Delineate Upslope Catchment

​		When delineating upslope catchments, a stack data structure is employed to accomplish depth-first traversal. While the stack is not empty, pop a pixel and mark it in the result layer, then push all its neighbor upslope pixels into the stack.

​		The program supports delineate multi-catchments at one time. The format of outlets could be coordinate array or a raster layer. If there are hydrological connection between input outlets, you can choose not to cover the upslope catchment result. At this condition, you can get inter-lake catchment if the format of the input outlets is a lake raster layer. 

​		Meanwhile, the stack could be reused when there are multi-catchments to be delineated, which reduces the consumption of memory alloction.

- Topology between Lakes

​		Along with the stream, find the direct downstream lakes of each lake and judge whether it is a terminal lake.

- Route between Lakes

​		When two lakes are hydrological-connected, build a flow path linestring along with the stream.