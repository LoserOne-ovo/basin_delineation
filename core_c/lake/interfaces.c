#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "interfaces.h"



/***********************************
 *          shared part            *
 ***********************************/


__declspec(dllexport) unsigned char* calc_reverse_fdir(unsigned char* fdir, int rows, int cols) {

	return _get_re_dir(fdir, rows, cols);
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


__declspec(dllexport) int paint_lake_hillslope_2_int32(int* lake, int max_lake_id, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols) {

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
