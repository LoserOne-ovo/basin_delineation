#include "interfaces.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>


/***********************************
 *          shared part            *
 ***********************************/

__declspec(dllexport) int32_t* label_4con(uint8_t* bin_ima, int32_t rows, int32_t cols, int32_t* label_num) {

	return _label_4con(bin_ima, rows, cols, label_num);
}

__declspec(dllexport) uint8_t* calc_reverse_fdir(uint8_t* fdir, int32_t rows, int32_t cols) {

	return _get_re_dir(fdir, rows, cols);
}

__declspec(dllexport) int32_t get_basin_envelope_uint8(uint8_t* basin, int32_t* envelopes, int32_t rows, int32_t cols) {

	return _get_basin_envelope_uint8(basin, envelopes, rows, cols);
}


__declspec(dllexport) int32_t get_basin_envelope_int32(int32_t* basin, int32_t* envelopes, int32_t rows, int32_t cols) {

	return _get_basin_envelope_int32(basin, envelopes, rows, cols);
}


/************************************
 *           island part            *
 ************************************/

__declspec(dllexport) int32_t island_statistic_int32(int32_t* island_label, int32_t island_num,	double* area, int32_t* envelope,
	uint8_t* dir, float* upa, int32_t rows, int32_t cols) {

	return _calc_island_statistics_int32(island_label, island_num, area, envelope, dir, upa, rows, cols);
}

__declspec(dllexport) int32_t get_basin_area(uint8_t* basin, double* basin_area, float* upa, int32_t rows, int32_t cols) {

	return _get_basin_area(basin, upa, basin_area, rows, cols);
}


__declspec(dllexport) int32_t island_paint_uint8(uint64_t* idxs, uint8_t* colors, int32_t island_num, uint8_t* dir,
	uint8_t* re_dir, uint8_t* basin, int32_t rows, int32_t cols) {
	return _island_paint_uint8(idxs, colors, island_num, dir, re_dir, basin, rows, cols);
}

__declspec(dllexport) int32_t island_paint_int32(uint64_t* idxs, int32_t* colors, int32_t island_num, uint8_t* dir,
	uint8_t* re_dir, int32_t* basin, int32_t rows, int32_t cols) {
	return _island_paint_int32(idxs, colors, island_num, dir, re_dir, basin, rows, cols);
}


__declspec(dllexport) int32_t get_coastal_line(uint64_t* idxs, uint8_t* colors, int32_t island_num, uint8_t* dir, 
	uint8_t* basin, int32_t rows, int32_t cols) {
	return _get_coastal_line(idxs, colors, island_num, dir, basin, rows, cols);
}


/***********************************
 *          outlet part            *
 ***********************************/

__declspec(dllexport) int32_t pfafstetter_uint8(uint64_t outlet_idx, uint64_t inlet_idx, uint8_t* re_dir, 
	float* upa, uint8_t* basin, float ths, int32_t rows, int32_t cols, int32_t* sub_outlets, int32_t* sub_intlets) {

	return _pfafstetter_uint8(outlet_idx, inlet_idx, re_dir, upa, basin, ths, rows, cols, sub_outlets, sub_intlets);
}

__declspec(dllexport) int32_t decompose_uint8(uint64_t outlet_idx, uint64_t inlet_idx, float area, int32_t decompose_num,
	uint8_t* dir, uint8_t* re_dir, float* upa, uint8_t* basin, int32_t rows, int32_t cols, int32_t* sub_outlets, int32_t* sub_inlets) {

	return _decompose_uint8(outlet_idx, inlet_idx, area, decompose_num, dir, re_dir, upa, basin, rows, cols, sub_outlets, sub_inlets);
}


/***********************************
 *           paint part            *
 ***********************************/


__declspec(dllexport) int32_t paint_up_uint8(uint64_t* idxs, uint8_t* colors, uint32_t idx_num, 
	uint8_t* basin, uint8_t* re_dir, int32_t rows, int32_t cols, double frac) {

	return _paint_up_uint8(idxs, colors, idx_num, basin, re_dir, rows, cols, frac);
}

__declspec(dllexport) int32_t paint_up_uint16(uint64_t* idxs, uint16_t* colors, uint32_t idx_num,
	uint16_t* basin, uint8_t* re_dir, int32_t rows, int32_t cols, double frac) {

	return _paint_up_uint16(idxs, colors, idx_num, basin, re_dir, rows, cols, frac);
}

__declspec(dllexport) int32_t paint_up_int32(uint64_t* idxs, int32_t* colors, uint32_t idx_num,
	int32_t* basin, uint8_t* re_dir, int32_t rows, int32_t cols, double frac) {

	return _paint_up_int32(idxs, colors, idx_num, basin, re_dir, rows, cols, frac);
}

__declspec(dllexport) int32_t paint_up_uint32(uint64_t* idxs, uint32_t* colors, uint32_t idx_num,
	uint32_t* basin, uint8_t* re_dir, int32_t rows, int32_t cols, double frac) {

	return _paint_up_uint32(idxs, colors, idx_num, basin, re_dir, rows, cols, frac);
}


__declspec(dllexport) int32_t paint_up_mosaiced_uint8(uint8_t* __restrict basin, uint8_t* __restrict re_dir, 
	int32_t rows, int32_t cols, double frac) {

	return _paint_up_mosaiced_uint8(basin, re_dir, rows, cols, frac);
}

__declspec(dllexport) int32_t paint_up_mosaiced_uint16(uint16_t* __restrict basin, uint8_t* __restrict re_dir,
	int32_t rows, int32_t cols, double frac) {

	return _paint_up_mosaiced_uint16(basin, re_dir, rows, cols, frac);
}


__declspec(dllexport) int32_t paint_up_mosaiced_int32(int32_t* __restrict basin, uint8_t* __restrict re_dir,
	int32_t rows, int32_t cols, double frac) {

	return _paint_up_mosaiced_int32(basin, re_dir, rows, cols, frac);
}


__declspec(dllexport) int32_t paint_up_mosaiced_uint32(uint32_t* __restrict basin, uint8_t* __restrict re_dir,
	int32_t rows, int32_t cols, double frac) {

	return _paint_up_mosaiced_uint32(basin, re_dir, rows, cols, frac);
}


//__declspec(dllexport) float* calc_single_pixel_upa(uint8_t* re_dir, float* upa, int32_t rows, int32_t cols) {
//
//	return _calc_single_pixel_upa(re_dir, upa, rows, cols);
//}


/***********************************
 *           sink part             *
 ***********************************/

__declspec(dllexport) int32_t dissolve_sinks_uint8(uint8_t* basin, uint8_t* re_dir, float* dem, uint64_t* sink_idxs,
	uint8_t sink_num, int32_t rows, int32_t cols, double frac) {

	return _dissolve_sinks_uint8(basin, re_dir, dem, sink_idxs, sink_num, rows, cols, frac);
}

__declspec(dllexport) int32_t dissolve_sinks_uint16(uint16_t* basin, uint8_t* re_dir, float* dem, uint64_t* sink_idxs,
	uint16_t sink_num, int32_t rows, int32_t cols, double frac) {

	return _dissolve_sinks_uint16(basin, re_dir, dem, sink_idxs, sink_num, rows, cols, frac);
}


__declspec(dllexport) int32_t sink_union_int32(int32_t* __restrict union_flag, int32_t* __restrict merge_flag, 
	int32_t sink_num, int32_t* __restrict basin, int32_t rows, int32_t cols) {

	return _sink_union(union_flag, merge_flag, sink_num, basin, rows, cols);
}


__declspec(dllexport) uint8_t find_attached_basin_uint8(uint64_t* sink_idxs, int32_t sink_num, uint8_t* re_dir,
	float* elv, uint8_t* basin, int32_t rows, int32_t cols) {

	return _find_attached_basin_uint8(sink_idxs, sink_num, re_dir, elv, basin, rows, cols);
}


__declspec(dllexport) uint8_t region_decompose_uint8(uint64_t* sink_idxs, float* sink_areas, int32_t sink_num, uint8_t* re_dir,
	float* elv, uint8_t* basin, int32_t rows, int32_t cols) {
	
	return _region_decompose_uint8(sink_idxs, sink_areas, sink_num, re_dir, elv,basin, rows, cols);
}


__declspec(dllexport) uint8_t region_decompose_uint8_2(uint64_t* sink_idxs, float* sink_areas, int32_t sink_num, uint8_t* re_dir,
	float* elv, uint8_t* basin, int32_t rows, int32_t cols) {

	return _region_decompose_uint8_2(sink_idxs, sink_areas, sink_num, re_dir, elv, basin, rows, cols);
}


__declspec(dllexport) int32_t sink_region(uint64_t* sink_idxs, float* sink_areas, int32_t sink_num,
	uint8_t* dir, int32_t rows, int32_t cols, int32_t* region_flag) {

	return _sink_region(sink_idxs, sink_areas, sink_num, dir, rows, cols, region_flag);
}



/***********************************
 *           lake part             *
 ***********************************/

 /****************************
  *   correct lake-stream    *
  ****************************/

__declspec(dllexport) int32_t correct_lake_stream_1(int32_t* lake, uint8_t* dir, uint8_t* re_dir, float* upa, float ths, int32_t rows, int32_t cols) {

	return _correct_lake_network_int32(lake, dir, re_dir, upa, ths, rows, cols);
}

__declspec(dllexport) int32_t correct_lake_stream_2(int32_t* lake, uint8_t* dir, uint8_t* re_dir, float* upa, float ths, int32_t rows, int32_t cols) {

	return _correct_lake_network_2_int32(lake, dir, re_dir, upa, ths, rows, cols);
}

/****************************
 *   paint lake hillslope   *
 ****************************/

__declspec(dllexport) int32_t paint_lake_hillslope_int32(int32_t* lake, int32_t max_lake_id, uint8_t* re_dir, float* upa, float ths, int32_t rows, int32_t cols) {

	return _paint_up_lake_hillslope_int32(lake, max_lake_id, re_dir, upa, ths, rows, cols);
}

__declspec(dllexport) int32_t paint_lake_hillslope_2_int32(int32_t* lake, int32_t max_lake_id, uint8_t* dir, uint8_t* re_dir, float* upa,
	float ths, int32_t rows, int32_t cols) {

	return _paint_up_lake_hillslope_2_int32(lake, max_lake_id, dir, re_dir, upa, ths, rows, cols);
}

__declspec(dllexport) int32_t paint_lake_hillslope_3_int32(int32_t* lake, int32_t max_lake_id, uint8_t* dir, uint8_t* re_dir, float* upa,
	float ths, int32_t rows, int32_t cols) {

	return _paint_up_lake_hillslope_3_int32(lake, max_lake_id, dir, re_dir, upa, ths, rows, cols);
}

__declspec(dllexport) int32_t* paint_lake_hillslope_new_int32(int32_t* lake, int32_t lake_num, uint8_t* dir, uint8_t* re_dir, float* upa,
	float ths, int32_t rows, int32_t cols, int32_t* return_basin_num) {

	return _paint_up_lake_hillslope_new(lake, lake_num, dir, re_dir, upa, ths, rows, cols, return_basin_num);
}


/****************************
 *   paint lake catchment   *
 ****************************/

__declspec(dllexport) int32_t paint_lake_local_catchment_int32(int32_t* lake, int32_t lake_num, uint8_t* re_dir, int32_t rows, int32_t cols) {

	return _paint_lake_local_catchment_int32(lake, lake_num, re_dir, rows, cols);
}

__declspec(dllexport) int32_t paint_lake_upper_catchment(int32_t* lake, int32_t lake_id, int32_t* board, uint8_t* re_dir, int32_t rows, int32_t cols) {

	return _paint_lake_upper_catchment_int32(lake, lake_id, board, re_dir, rows, cols);
}


__declspec(dllexport) int32_t paint_single_lake_catchment(uint8_t* lake, uint8_t* re_dir, int32_t rows, int32_t cols,
	int32_t min_row, int32_t min_col, int32_t max_row, int32_t max_col) {

	return _paint_single_lake_catchment(lake, re_dir, rows, cols, min_row, min_col, max_row, max_col);
}



/****************************
 *   create lake topology   *
 ****************************/

__declspec(dllexport) int32_t mark_lake_outlet_int32(int32_t* lake, int32_t min_lake_id, int32_t max_lake_id, uint8_t* dir, int32_t rows, int32_t cols) {

	return _mark_lake_outlet_int32(lake, min_lake_id, max_lake_id, dir, rows, cols);
}

__declspec(dllexport) int32_t* create_lake_topology(int32_t* water, int32_t lake_num, int32_t* tag_array, uint8_t* dir, int32_t rows, int32_t cols) {

	return _topology_between_lakes(water, lake_num, tag_array, dir, rows, cols);
}

__declspec(dllexport) uint64_t* create_route_between_lake(int32_t* lake, int32_t lake_num, uint8_t* dir, float* upa, int32_t rows, int32_t cols,
	int32_t* re_num, uint64_t* re_length) {

	return _route_between_lake(lake, lake_num, dir, upa, rows, cols, re_num, re_length);
}



/***********************************
 *           river part            *
 ***********************************/

__declspec(dllexport) int32_t* define_network(uint8_t* dir, float* upa, float ths, int32_t outlet_ridx, int32_t outlet_cidx, int32_t rows, int32_t cols) {

	return _dfn_stream(dir, upa, ths, outlet_ridx, outlet_cidx, rows, cols);
}

__declspec(dllexport) int32_t paint_river_hillslope_int32(int32_t* stream, int32_t min_channel_id, int32_t max_channel_id, uint8_t* dir, uint8_t* re_dir, int32_t rows, int32_t cols) {

	return _paint_river_hillslope_int32(stream, min_channel_id, max_channel_id, dir, re_dir, rows, cols);
}
__declspec(dllexport) int32_t check_on_mainstream(int32_t t_ridx, int32_t t_cidx, int32_t inlet_ridx, int32_t inlet_cidx, uint8_t inlet_dir, uint8_t* dir, int32_t cols) {

	return _check_on_mainstream(t_ridx, t_cidx, inlet_ridx, inlet_cidx, inlet_dir, dir, cols);
}


__declspec(dllexport) int32_t delineate_sub_basin_hillslope(uint8_t* __restrict stream, uint8_t* __restrict dir, 
	int32_t rows, int32_t cols, uint8_t nodata) {
	return _delineate_basin_hillslope(stream, dir, rows, cols, nodata);
}

