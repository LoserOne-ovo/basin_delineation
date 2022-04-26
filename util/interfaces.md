**Here are descriptions of some meaningful functions.**

- **calc_reverse_dir(dir_arr)**

​		Calculate the reverse d8 flow direction, which is crucial part of quick catchment delineation. Each bit represents whether there are upstream pixels in the corresponding direction.

- **label**

​        Four connected domain analysis of binary images.

- **pfafstetter**

​        Divide a basin into up to 9 sub-basins.

- **paint_up_uint8**

​        Delineate the upstream catchment of input pixels.

- **paint_lake_local_catchment_int32_c**

​		Delineate the inter-lake catchment.

- **create_lake_topology_int32_c**

​		Calculate the upstream and downstream relationship between lakes.

- **create_route_between_lake_c**

​		Calculate the flow path between lakes.