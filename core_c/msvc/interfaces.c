#include "interfaces.h"
#include "type_aka.h"
#include <stdio.h>
#include <stdlib.h>


/***********************************
 *          shared part            *
 ***********************************/

__declspec(dllexport) unsigned int* label_4con(unsigned char* bin_ima, int rows, int cols, unsigned int* label_num) {

	return _label_4con(bin_ima, rows, cols, label_num);
}

__declspec(dllexport) unsigned char* calc_reverse_fdir(unsigned char* fdir, int rows, int cols) {

	return _get_re_dir(fdir, rows, cols);
}

__declspec(dllexport) int get_basin_envelope_uint8(unsigned char* basin, int* envelopes, int rows, int cols) {

	return _get_basin_envelope_uint8(basin, envelopes, rows, cols);
}


/************************************
 *           island part            *
 ************************************/

__declspec(dllexport) int island_statistic_uint32(unsigned int* island_label, unsigned int island_num, float* center, int* sample,
	float* area, float* ref_area, int* envelope, unsigned char* dir, float* upa, int rows, int cols) {

	return _calc_island_statistics_uint32(island_label, island_num, center, sample, area, ref_area, envelope, dir, upa, rows, cols);
}

__declspec(dllexport) int update_island_label_uint32(unsigned int* island_label, unsigned int* new_label, unsigned int island_num, int rows, int cols) {

	return _update_island_label_uint32(island_label, island_num, new_label, rows, cols);
}


__declspec(dllexport) int island_merge_uint8(float* center_ridx, float* center_cidx, float* radius, int island_num, unsigned char* merge_flag) {

	return _island_merge(center_ridx, center_cidx, radius, island_num, merge_flag);
}


/***********************************
 *          outlet part            *
 ***********************************/

__declspec(dllexport) int pfafstetter(int outlet_ridx, int outlet_cidx, unsigned char* basin, unsigned char* re_dir, float* upa,
									  int* sub_outlets, float ths, int rows, int cols) {

	return _pfs_r_uint8(outlet_ridx, outlet_cidx, basin, re_dir, upa, sub_outlets, ths, rows, cols);
}



/***********************************
 *           paint part            *
 ***********************************/

__declspec(dllexport) int paint_up_uint8(unsigned long long* idxs, unsigned char* colors, unsigned int idx_num, double frac,
										 unsigned char* basin, unsigned char* re_dir, int rows, int cols) {

	return _paint_up_uint8(idxs, colors, idx_num, frac, basin, re_dir, rows, cols);
}

__declspec(dllexport) int paint_up_uint32(unsigned long long* idxs, unsigned int* colors, unsigned int idx_num, double frac,
	unsigned int* basin, unsigned char* re_dir, int rows, int cols) {

	return _paint_up_uint32(idxs, colors, idx_num, frac, basin, re_dir, rows, cols);
}


__declspec(dllexport) int paint_up_mosaiced_uint8(int* ridx, int* cidx, unsigned int num, double frac, unsigned char* basin,
	unsigned char* re_dir, int rows, int cols) {


	uint64 cols64 = (uint64)cols;
	uint64* idxs_1D = (uint64*)calloc(num, sizeof(unsigned long long));
	if (idxs_1D == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint i = 0; i < num; i++) {
		idxs_1D[i] = ridx[i] * cols64 + cidx[i];
	}

	uint8* colors = (uint8*)calloc(num, sizeof(unsigned char));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint i = 0; i < num; i++) {
		colors[i] = basin[idxs_1D[i]];
	}

	int res = _paint_up_uint8(idxs_1D, colors, num, frac, basin, re_dir, rows, cols);
	free(idxs_1D);
	free(colors);

	return res;
}

__declspec(dllexport) float* calc_single_pixel_upa(unsigned char* re_dir, float* upa, int rows, int cols) {

	return _calc_single_pixel_upa(re_dir, upa, rows, cols);
}


/***********************************
 *           sink part             *
 ***********************************/

__declspec(dllexport) int dissolve_sinks_uint8(unsigned char* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
	unsigned char sink_num, int rows, int cols, double frac) {

	return _dissolve_sinks_uint8(basin, re_dir, dem, sink_idxs, sink_num, rows, cols, frac);
}

__declspec(dllexport) int dissolve_sinks_uint16(unsigned short* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
	unsigned short sink_num, int rows, int cols, double frac) {

	return _dissolve_sinks_uint16(basin, re_dir, dem, sink_idxs, sink_num, rows, cols, frac);
}



/***********************************
 *           lake part             *
 ***********************************/

 /****************************
  *   correct lake-stream    *
  ****************************/

__declspec(dllexport) int correct_lake_stream_1(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols) {

	return _correct_lake_network_int32(lake, dir, re_dir, upa, ths, rows, cols);
}

__declspec(dllexport) int correct_lake_stream_2(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols) {

	return _correct_lake_network_2_int32(lake, dir, re_dir, upa, ths, rows, cols);
}

/****************************
 *   paint lake hillslope   *
 ****************************/

__declspec(dllexport) int paint_lake_hillslope_int32(int* lake, int max_lake_id, unsigned char* re_dir, float* upa, float ths, int rows, int cols) {

	return _paint_up_lake_hillslope_int32(lake, max_lake_id, re_dir, upa, ths, rows, cols);
}

__declspec(dllexport) int paint_lake_hillslope_2_int32(int* lake, int max_lake_id, unsigned char* dir, unsigned char* re_dir, float* upa, 
	float ths, int rows, int cols) {

	return _paint_up_lake_hillslope_2_int32(lake, max_lake_id, dir, re_dir, upa, ths, rows, cols);
}

/****************************
 *   paint lake catchment   *
 ****************************/

__declspec(dllexport) int paint_lake_local_catchment_int32(int* lake, int lake_num, unsigned char* re_dir, int rows, int cols) {

	return _paint_lake_local_catchment_int32(lake, lake_num, re_dir, rows, cols);
}

__declspec(dllexport) int paint_lake_upper_catchment(int* lake, int lake_id, int* board, unsigned char* re_dir, int rows, int cols) {

	return _paint_lake_upper_catchment_int32(lake, lake_id, board, re_dir, rows, cols);
}


/****************************
 *   create lake topology   *
 ****************************/

__declspec(dllexport) int mark_lake_outlet_int32(int* lake, int min_lake_id, int max_lake_id, unsigned char* dir, int rows, int cols) {

	return _mark_lake_outlet_int32(lake, min_lake_id, max_lake_id, dir, rows, cols);
}

__declspec(dllexport) int* create_lake_topology(int* water, int lake_num, int* tag_array, unsigned char* dir, int rows, int cols) {

	return _topology_between_lakes(water, lake_num, tag_array, dir, rows, cols);
}

__declspec(dllexport) unsigned long long* create_route_between_lake(int* lake, int lake_num, unsigned char* dir, float* upa, int rows, int cols,
	int* re_num, unsigned long long* re_length) {

	return _route_between_lake(lake, lake_num, dir, upa, rows, cols, re_num, re_length);
}



/***********************************
 *           river part            *
 ***********************************/

__declspec(dllexport) int* define_network(unsigned char* dir, float* upa, float ths, int outlet_ridx, int outlet_cidx, int rows, int cols) {

	return _dfn_stream(dir, upa, ths, outlet_ridx, outlet_cidx, rows, cols);
}

__declspec(dllexport) int paint_river_hillslope_int32(int* stream, int min_channel_id, int max_channel_id, unsigned char* dir, unsigned char* re_dir, int rows, int cols) {

	return _paint_river_hillslope_int32(stream, min_channel_id, max_channel_id, dir, re_dir, rows, cols);
}
__declspec(dllexport) int check_on_mainstream(int t_ridx, int t_cidx, int inlet_ridx, int inlet_cidx, unsigned char inlet_dir, unsigned char* dir, int cols) {

	return _check_on_mainstream(t_ridx, t_cidx, inlet_ridx, inlet_cidx, inlet_dir, dir, cols);
}

