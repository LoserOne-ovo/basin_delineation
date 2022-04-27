**Here are descriptions of some meaningful functions.**

- **calc_reverse_dir**

​		Calculate the reverse d8 flow direction, which is crucial part of quick catchment delineation. Each bit represents whether there are upstream pixels in the corresponding direction.

-   **Parameters:**

- ***dir_arr**  :  np.ndarray (dim=2, dtype=np.uint8)*

​										d8 flow direction

-   **Returns:** 

***re_dir_arr**  :  np.ndarray (dim=2, dtype=np.uint8)*

​										reversed d8 flow direction, share the same shape with dir_arr

- **label**

​        Four connected domain analysis of binary images.

​		**Parameters:**    ***bin_image***  *:  np.ndarray (dim=2, dtype=np.uint8)*

​										binary image, only one channel

​		**Returns:**           ***label_res**  :  np.ndarray (dim=2, dtype=np.uint32)*

​										labelled array, where the 4-neighbour connected pixels share the same value 
​		                           ***label_num**  :  int*

​										the number of 4-connected domains 

- **pfafstetter**

​        Divide a basin into up to 9 sub-basins.

​		**Parameters:**    ***outlet_idx***  *:  tuple(int, int)*

​										Location of the outlet in the image

​		                           ***basin_arr**  :  np.ndarray (dim=2, dtype=np.uint8)*

​										result layer to show the spatial distribution of sub-basins

​		                           ***re_dir_arr**  :  np.ndarray (dim=2, dtype=np.uint8)*

​										reversed d8 flow direction, share the same shape with basin_arr

​		                           ***upa_arr**  :  np.ndarray (dim=2, dtype=np.float32)*

​										upslope catchment area, share the same shape with basin_arr

​		                           ***sub_outlets**  :  np.ndarray (shape=(11,2), dtype=np.int32)*

​										store of outlets of the delineated sub-basins

​		                           ***ths**  :  float*

​										threshold of upslope catchment area above which a pixel could be considered as stream

​		**Returns:**           ***sub_num**  :  int*

​										the number of the delineated sub-basins

- **paint_up_uint8**

​        Delineate the upstream catchment of input pixels.

​		**Parameters:**    ***idx_arr***  *:  np.ndarray (shape=(x,2), dtype=np.int32)*

​										Locations of the outlets in the image

​		                           ***colors**  :  np.ndarray (shape=(x,), dtype=np.uint8)*

​										the id of each outlet

​		                           ***re_dir_arr**  :  np.ndarray (dim=2, dtype=np.uint8)*

​										reversed d8 flow direction, share the same shape with basin_arr

​		                           ***basin_arr**  :  np.ndarray (dim=2, dtype=np.float32)*

​										result layer to show the spatial distribution of different delineated catchments

​		**Returns:**           ***flag**  :  int*

​										1

- **paint_lake_local_catchment_int32_c**

​		Delineate the inter-lake catchment.

​		The bound of a lake's inter lake-catchment includes the lake pixels and the other pixels which flow into the lake directly without flowing through other lakes. 

​		**Parameters:**    ***lake_arr***  *:  np.ndarray (dim=2, dtype=np.int32)*

​										source layer with lake-value burned and result layer which shows the spatial distribution of different delineated catchments at the same time

​		                           ***max_lake_id**  :  int*

​										only the pixels with value in [1, max_lake_id] will be seen as a lake pixel

​		                           ***re_dir_arr**  :  np.ndarray (dim=2, dtype=np.uint8)*

​										reversed d8 flow direction, share the same shape with lake_arr

​		**Returns:**           ***flag**  :  int*

​										1

- **create_lake_topology_int32_c**

​		Calculate the upstream and downstream relationship between lakes.

​		**Parameters:**    ***lake_arr***  *:  np.ndarray (dim=2, dtype=np.int32)*

​										source layer with lake-value burned

​		                           ***lake_num**  :  int*

​										equals to max_lake_id

​		                           ***dir_arr**  :  np.ndarray (dim=2, dtype=np.uint8)*

​										d8 flow direction

​		**Returns:**           ***down_lake_arr**  :  np.ndarray (dim=1, dtype=np.int32)*

​										merge the down lake id of each lake into a 1-dimension array

​		                           ***block_arr**  :  np.ndarray (shape=(lake_num,), dtype=np.int32)*

​										store the number of down lakes of each lake 

- **create_route_between_lake_c**

​		Calculate the flow path between lakes.

​		**Parameters:**    ***lake_arr***  *:  np.ndarray (dim=2, dtype=np.int32)*

​										source layer with lake-value burned

​		                           ***lake_num**  :  int*

​										equals to max_lake_id

​		                           ***dir_arr**  :  np.ndarray (dim=2, dtype=np.uint8)*

​										d8 flow direction

​		                           ***upa_arr**  :  np.ndarray (dim=2, dtype=np.float32)*

​										upslope catchment area, share the same shape with basin_arr

​		**Returns:**           ***result_arr**  :  np.ndarray (dim=1, dtype=np.uint64)*

​										merge the routes between lakes into a 1-dimension array

​		                           ***block_arr**  :  np.ndarray (shape=(lake_num,), dtype=np.int32)*

​										store the number of routes 