#ifndef _INTERFACES_H_
#define _INTERFACES_H_

#include <stdint.h>


/***********************************
 *          shared part            *
 ***********************************/

uint8_t* _get_re_dir(uint8_t* __restrict fdir, int32_t rows, int32_t cols);
int32_t* _label_4con(uint8_t* __restrict bin_ima, int32_t rows, int32_t cols, int32_t* label_num);
int32_t _get_basin_envelope_uint8(uint8_t* __restrict basin, int32_t* envelopes, int32_t rows, int32_t cols);
int32_t _get_basin_envelope_int32(int32_t* __restrict basin, int32_t* envelopes, int32_t rows, int32_t cols);


/***********************************
 *          island part            *
 ***********************************/

 // 统计岛屿相关属性
int32_t _calc_island_statistics_int32(int32_t* __restrict island_label, int32_t island_num, double* __restrict area, int32_t* __restrict envelope,
	uint8_t* __restrict dir, float* __restrict upa, int32_t rows, int32_t cols);

int32_t _island_paint_uint8(uint64_t* __restrict idxs, uint8_t* __restrict colors, int32_t island_num, uint8_t* __restrict dir,
	uint8_t* __restrict re_dir, uint8_t* __restrict basin, int32_t rows, int32_t cols);

int32_t _island_paint_int32(uint64_t* __restrict idxs, int32_t* __restrict colors, int32_t island_num, uint8_t* __restrict dir,
	uint8_t* __restrict re_dir, int32_t* __restrict basin, int32_t rows, int32_t cols);

int32_t _get_basin_area(uint8_t* __restrict basin, float* __restrict upa, double* __restrict basin_area, int32_t rows, int32_t cols);

int32_t _get_coastal_line(uint64_t* __restrict idxs, uint8_t* __restrict colors, int32_t island_num, uint8_t* __restrict dir,
	uint8_t* __restrict edge, int32_t rows, int32_t cols);

/***********************************
 *          outlet part            *
 ***********************************/

int32_t _pfafstetter_uint8(uint64_t outlet_idx, uint64_t inlet_idx, uint8_t* __restrict re_dir, float* __restrict upa,
	uint8_t* __restrict basin, float ths, int32_t rows, int32_t cols, int32_t* __restrict sub_outlets, int32_t* __restrict sub_intlets);

int32_t _decompose_uint8(uint64_t outlet_idx, uint64_t inlet_idx, float area, int32_t decompose_num,
	uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa, uint8_t* __restrict basin,
	int32_t rows, int32_t cols, int32_t* __restrict sub_outlets, int32_t* __restrict sub_inlets);

/***********************************
 *           paint part            *
 ***********************************/

#include "paint_up.h"


/***********************************
 *           sink part             *
 ***********************************/

int32_t _dissolve_sinks_uint8(uint8_t* __restrict basin, uint8_t* __restrict re_dir, float* __restrict dem, uint64_t* __restrict sink_idxs,
	uint8_t sink_num, int32_t rows, int32_t cols, double frac);

int32_t _dissolve_sinks_uint16(uint16_t* __restrict basin, uint8_t* __restrict re_dir, float* __restrict dem, uint64_t* __restrict sink_idxs,
	uint16_t sink_num, int32_t rows, int32_t cols, double frac);

int32_t _sink_union(int32_t* __restrict union_flag, int32_t* __restrict merge_flag, int32_t sink_num, int32_t* __restrict basin, int32_t rows, int32_t cols);


uint8_t _find_attached_basin_uint8(uint64_t* __restrict sink_idxs, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, int32_t rows, int32_t cols);


uint8_t _region_decompose_uint8(uint64_t* __restrict sink_idxs, float* __restrict sink_areas, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, int32_t rows, int32_t cols);


uint8_t _region_decompose_uint8_2(uint64_t* __restrict sink_idxs, float* __restrict sink_areas, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, int32_t rows, int32_t cols);


int32_t _sink_region(uint64_t* __restrict sink_idxs, float* __restrict sink_areas, int32_t sink_num,
	uint8_t* __restrict dir, int32_t rows, int32_t cols, int32_t* __restrict region_flag);




/***********************************
 *           lake part             *
 ***********************************/

int32_t _correct_lake_network_int32(int32_t* __restrict lake, uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols);
int32_t _correct_lake_network_2_int32(int32_t* __restrict lake, uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols);

int32_t _paint_up_lake_hillslope_int32(int32_t* __restrict lake, int32_t lake_num, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols);
int32_t _paint_up_lake_hillslope_2_int32(int32_t* __restrict lake, int32_t max_lake_id, uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa,
	float ths, int32_t rows, int32_t cols);
int32_t _paint_up_lake_hillslope_3_int32(int32_t* __restrict lake, int32_t max_lake_id, uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa,
	float ths, int32_t rows, int32_t cols);

int32_t _paint_lake_local_catchment_int32(int32_t* __restrict lake, int32_t lake_num, uint8_t* __restrict re_dir, int32_t rows, int32_t cols);
int32_t _paint_lake_upper_catchment_int32(int32_t* __restrict lake, int32_t lake_id, int32_t* __restrict board, uint8_t* __restrict re_dir, int32_t rows, int32_t cols);
int32_t* _topology_between_lakes(int32_t* __restrict water, int32_t lake_num, int32_t* __restrict tag_array, uint8_t* __restrict dir, int32_t rows, int32_t cols);

int32_t _find_next_water_body_int32(uint64_t idx, int32_t* __restrict water, uint8_t* __restrict dir, int32_t cols);
int32_t _mark_lake_outlet_int32(int32_t* __restrict lake, int32_t min_lake_id, int32_t max_lake_id, uint8_t* __restrict dir, int32_t rows, int32_t cols);
uint64_t* _route_between_lake(int32_t* __restrict lake, int32_t lake_num, uint8_t* __restrict dir, float* __restrict upa, int32_t rows, int32_t cols,
	int32_t* return_num, uint64_t* return_length);


int32_t* _paint_up_lake_hillslope_new(int32_t* __restrict lake, int32_t lake_num, uint8_t* __restrict dir,
	uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols, int32_t* return_basin_num);


int32_t _paint_single_lake_catchment(uint8_t* __restrict lake, uint8_t* __restrict re_dir, int32_t rows, int32_t cols,
	int32_t min_row, int32_t min_col, int32_t max_row, int32_t max_col);


/***********************************
 *           river part            *
 ***********************************/

int32_t* _dfn_stream(uint8_t* __restrict dir, float* __restrict upa, float ths, int32_t outlet_ridx, int32_t outlet_cidx, int32_t rows, int32_t cols);
int32_t _paint_river_hillslope_int32(int32_t* __restrict stream, int32_t min_channel_id, int32_t max_channel_id, uint8_t* __restrict dir,
	uint8_t* __restrict re_dir, int32_t rows, int32_t cols);
int32_t _check_on_mainstream(int32_t t_ridx, int32_t t_cidx, int32_t inlet_ridx, int32_t inlet_cidx, uint8_t inlet_dir, uint8_t* dir, int32_t cols);



int32_t _delineate_basin_hillslope(uint8_t* __restrict stream, uint8_t* __restrict dir,
	int32_t rows, int32_t cols, uint8_t nodata);



#endif // !_INTERFACES_H_
