#ifndef _INTERFACES_H_
#define _INTERFACES_H_


/***********************************
 *          shared part            *
 ***********************************/

unsigned char* _get_re_dir(unsigned char* fdir, int rows, int cols);
unsigned int* _label_4con(unsigned char* bin_ima, int rows, int cols, unsigned int* label_num);
int _get_basin_envelope_uint8(unsigned char* basin, int* envelopes, int rows, int cols);



/***********************************
 *          island part            *
 ***********************************/

 // 统计岛屿相关属性
int _calc_island_statistics_uint32(unsigned int* island_label, unsigned int island_num, float* center, int* sample,
	float* area, float* ref_area, int* envelope, unsigned char* dir, float* upa, int rows, int cols);
int _update_island_label_uint32(unsigned int* island_label, unsigned int island_num, unsigned int* new_label, int rows, int cols);



/***********************************
 *          outlet part            *
 ***********************************/

int _pfs_r_uint8(int outlet_ridx, int outlet_cidx, unsigned char* basin, unsigned char* re_dir, float* upa,
				 int* sub_outlets, float ths, int rows, int cols);


/***********************************
 *           paint part            *
 ***********************************/

int _paint_up_uint8(unsigned long long* idxs, unsigned char* colors, unsigned int idx_num, double frac, 
					unsigned char* basin, unsigned char* re_dir, int rows, int cols);
float* _calc_single_pixel_upa(unsigned char* re_dir, float* upa, int rows, int cols);


/***********************************
 *           sink part             *
 ***********************************/

int _dissolve_sinks_uint8(unsigned char* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
	unsigned char sink_num, int rows, int cols, double frac);

int _dissolve_sinks_uint16(unsigned short* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
	unsigned short sink_num, int rows, int cols, double frac);



/***********************************
 *           lake part             *
 ***********************************/

int _correct_lake_network_int32(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols);
int _correct_lake_network_2_int32(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols);

int _paint_up_lake_hillslope_int32(int* lake, int lake_num, unsigned char* re_dir, float* upa, float ths, int rows, int cols);
int _paint_up_lake_hillslope_2_int32(int* lake, int max_lake_id, unsigned char* dir, unsigned char* re_dir, float* upa,
	float ths, int rows, int cols);

int _paint_lake_local_catchment_int32(int* lake, int lake_num, unsigned char* re_dir, int rows, int cols);
int _paint_lake_upper_catchment_int32(int* lake, int lake_id, int* board, unsigned char* re_dir, int rows, int cols);
int* _topology_between_lakes(int* water, int lake_num, int* tag_array, unsigned char* dir, int rows, int cols);

int _find_next_water_body_int32(unsigned long long idx, int* water, unsigned char* dir, int cols);
int _mark_lake_outlet_int32(int* lake, int min_lake_id, int max_lake_id, unsigned char* dir, int rows, int cols);
unsigned long long* _route_between_lake(int* lake, int lake_num, unsigned char* dir, float* upa, int rows, int cols, 
	int* return_num, unsigned long long* return_length);



/***********************************
 *           river part            *
 ***********************************/

int* _dfn_stream(unsigned char* dir, float* upa, float ths, int outlet_ridx, int outlet_cidx, int rows, int cols);
int _paint_river_hillslope_int32(int* stream, int min_channel_id, int max_channel_id, unsigned char* dir, 
	unsigned char* re_dir, int rows, int cols);


#endif // !_INTERFACES_H_
