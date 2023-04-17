#ifndef _SINKS_H_
#define _SINKS_H_

#include "Array.h"



//typedef struct {
//	int32_t region_num;
//	i32_DynArray** regions;
//}Regions;



int32_t _dissolve_sinks_uint16(uint16_t* __restrict basin, uint8_t* __restrict re_dir, float* __restrict dem, uint64_t* __restrict sink_idxs,
						   uint16_t sink_num, int32_t rows, int32_t cols, double frac);
uint16_t* _inner_merge_u16(uint16_t* __restrict basin, float* __restrict elev, u64_DynArray** rim_cell,
								 uint16_t sink_num, uint16_t min_sink, const int32_t offset[]);
u64_DynArray* _remove_inner_peak_u16(u64_DynArray* src, uint16_t* basin, u16_DynArray* cur_color, const int32_t offset[]);
u64_DynArray* _eL_merge_u16(u64_DynArray* __restrict src, u64_DynArray* __restrict ins, uint16_t* basin, u16_DynArray* cur_basin, const int32_t offset[]);
uint16_t _find_next_basin_u16(u64_DynArray* edge_list, float* elev, uint16_t* basin, u16_DynArray* cur_basin, const int32_t offset[]);


int32_t _dissolve_sinks_uint8(uint8_t* __restrict basin, uint8_t* __restrict re_dir, float* __restrict dem, uint64_t* __restrict sink_idxs,
						  uint8_t sink_num, int32_t rows, int32_t cols, double frac);
uint8_t* _inner_merge_u8(uint8_t* __restrict basin, float* __restrict elev, u64_DynArray** rim_cell,
							   uint8_t sink_num, uint8_t min_sink, const int32_t offset[]);
u64_DynArray* _remove_inner_peak_u8(u64_DynArray* src, uint8_t* basin, u8_DynArray* cur_color, const int32_t offset[]);
u64_DynArray* _eL_merge_u8(u64_DynArray* __restrict src, u64_DynArray* __restrict ins, uint8_t* basin, u8_DynArray* cur_basin, const int32_t offset[]);
uint8_t _find_next_basin_u8(u64_DynArray* edge_list, float* elev, uint8_t* basin, u8_DynArray* cur_basin, const int32_t offset[]);


uint8_t _find_attached_basin_uint8(uint64_t* __restrict sink_idxs, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, int32_t rows, int32_t cols);
uint8_t _find_attached_basin_uint8_core(uint64_t* __restrict sink_idxs, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, u64_DynArray* stack, const int32_t* offset, const uint8_t* div);


uint8_t _region_decompose_uint8(uint64_t* __restrict sink_idxs, float* __restrict sink_areas, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, int32_t rows, int32_t cols);
uint8_t** _create_sink_adjacentMatrix(int32_t sink_num, int32_t* __restrict basin, int rows, int cols);
int32_t _region_decompose_uint8_core(float* __restrict sink_areas, int32_t sink_num, float total_area, uint8_t expected_num,
	uint8_t* __restrict region_flag, int32_t* __restrict dstFromCorner, uint8_t** __restrict adjacentMatrix);
int32_t _find_a_corner_sink(int32_t sink_num, uint8_t* __restrict region_flag, int32_t* __restrict dstFromCorner);
int32_t _find_a_corner_sink_from_neighbours(float* __restrict sink_areas, int32_t sink_num, float left_area,
	i32_DynArray* __restrict nbs, int32_t* __restrict dstFromCorner);


uint8_t _region_decompose_uint8_2(uint64_t* __restrict sink_idxs, float* __restrict sink_areas, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, int32_t rows, int32_t cols);
uint8_t _region_decompose_uint8_core_2(int32_t* __restrict cur_sinks, int32_t cur_sink_num, float cur_total_area, uint8_t cur_expected_num, uint8_t sub_num,
	float* __restrict sink_areas, uint8_t* __restrict region_flag, int32_t* __restrict dstFromCorner, uint8_t** __restrict adjacentMatrix);
i32_DynArray** _get_sub_regions_2(int32_t* __restrict cur_sinks, int32_t cur_sink_num, int* region_num, uint8_t** __restrict adjacentMatrix, uint8_t* __restrict region_flag);
int32_t _find_a_corner_sink_2(int32_t* __restrict cur_sinks, int32_t cur_sink_num, uint8_t* __restrict region_flag, int32_t* __restrict dstFromCorner);
int32_t _find_a_corner_sink_from_neighbours_2(float left_area, float* __restrict sink_areas, i32_DynArray* __restrict nbs, int32_t* __restrict dstFromCorner);


int32_t _sink_region(uint64_t* __restrict sink_idxs, float* __restrict sink_areas, int32_t sink_num,
	uint8_t* __restrict dir, int32_t rows, int32_t cols, int32_t* __restrict region_flag);


#endif
