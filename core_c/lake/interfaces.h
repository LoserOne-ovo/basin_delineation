#ifndef _INTERFACES_H_
#define _INTERFACES_H_



/***********************************
 *          shared part            *
 ***********************************/

unsigned char* _get_re_dir(unsigned char* fdir, int rows, int cols);



/***********************************
 *           lake part             *
 ***********************************/

int _correct_lake_network_int32(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols);
int _correct_lake_network_2_int32(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols);

int _paint_up_lake_hillslope_int32(int* lake, int lake_num, unsigned char* re_dir, float* upa, float ths, int rows, int cols);
int _paint_up_lake_hillslope_2_int32(int* lake, int max_lake_id, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols);
int _paint_lake_local_catchment_int32(int* lake, int lake_num, unsigned char* re_dir, int rows, int cols);
int _paint_lake_upper_catchment_int32(int* lake, int lake_id, int* board, unsigned char* re_dir, int rows, int cols);

int* _topology_between_lakes(int* water, int lake_num, int* tag_array, unsigned char* dir, int rows, int cols);
int _find_next_water_body_int32(unsigned long long idx, int* water, unsigned char* dir, int cols);
int _mark_lake_outlet_int32(int* lake, int min_lake_id, int max_lake_id, unsigned char* dir, int rows, int cols);




#endif // !_INTERFACES_H_
