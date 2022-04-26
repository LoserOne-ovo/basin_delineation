#ifndef _INTERFACES_H_
#define _INTERFACES_H_


/***********************************
 *          shared part            *
 ***********************************/

unsigned char* _get_re_dir(unsigned char*__restrict fdir, int rows, int cols);
unsigned int* _label_4con(unsigned char* __restrict bin_ima, int rows, int cols, unsigned int* label_num);
int _get_basin_envelope_uint8(unsigned char* __restrict basin, int* envelopes, int rows, int cols);



/***********************************
 *          island part            *
 ***********************************/

 // 统计岛屿相关属性
int _calc_island_statistics_uint32(unsigned int* __restrict island_label, unsigned int island_num, float* __restrict center, int* __restrict sample,
	float* __restrict area, float* __restrict ref_area, int* __restrict envelope, unsigned char* __restrict dir, float* __restrict upa, int rows, int cols);
int _update_island_label_uint32(unsigned int* __restrict island_label, unsigned int island_num, unsigned int* __restrict new_label, int rows, int cols);
int _island_merge(float* __restrict center_ridx, float* __restrict center_cidx, float* __restrict radius,
	int island_num, unsigned char* merge_flag);


/***********************************
 *          outlet part            *
 ***********************************/

int _pfs_r_uint8(int outlet_ridx, int outlet_cidx, unsigned char* __restrict basin, unsigned char* __restrict re_dir, float* __restrict upa,
				 int* sub_outlets, float ths, int rows, int cols);


/***********************************
 *           paint part            *
 ***********************************/

int _paint_up_uint8(unsigned long long* __restrict idxs, unsigned char* __restrict colors, unsigned int idx_num, double frac,
					unsigned char* __restrict basin, unsigned char* __restrict re_dir, int rows, int cols);
int _paint_up_uint16(unsigned long long* __restrict idxs, unsigned short* __restrict colors, unsigned int idx_num, double frac,
	unsigned short* __restrict basin, unsigned char* __restrict re_dir, int rows, int cols);
int _paint_up_uint32(unsigned long long* __restrict idxs, unsigned int* __restrict colors, unsigned int idx_num, double frac,
	unsigned int* __restrict basin, unsigned char* __restrict re_dir, int rows, int cols);
float* _calc_single_pixel_upa(unsigned char* __restrict re_dir, float* __restrict upa, int rows, int cols);


/***********************************
 *           sink part             *
 ***********************************/

int _dissolve_sinks_uint8(unsigned char* __restrict basin, unsigned char* __restrict re_dir, float* __restrict dem, unsigned long long* __restrict sink_idxs,
	unsigned char sink_num, int rows, int cols, double frac);

int _dissolve_sinks_uint16(unsigned short* __restrict basin, unsigned char* __restrict re_dir, float* __restrict dem, unsigned long long* __restrict sink_idxs,
	unsigned short sink_num, int rows, int cols, double frac);



/***********************************
 *           lake part             *
 ***********************************/

int _correct_lake_network_int32(int* __restrict lake, unsigned char* __restrict dir, unsigned char* __restrict re_dir, float* __restrict upa, float ths, int rows, int cols);
int _correct_lake_network_2_int32(int* __restrict lake, unsigned char* __restrict dir, unsigned char* __restrict re_dir, float* __restrict upa, float ths, int rows, int cols);

int _paint_up_lake_hillslope_int32(int* __restrict lake, int lake_num, unsigned char* __restrict re_dir, float* __restrict upa, float ths, int rows, int cols);
int _paint_up_lake_hillslope_2_int32(int* __restrict lake, int max_lake_id, unsigned char* __restrict dir, unsigned char* __restrict re_dir, float* __restrict upa,
	float ths, int rows, int cols);

int _paint_lake_local_catchment_int32(int* __restrict lake, int lake_num, unsigned char* __restrict re_dir, int rows, int cols);
int _paint_lake_upper_catchment_int32(int* __restrict lake, int lake_id, int* __restrict board, unsigned char* __restrict re_dir, int rows, int cols);
int* _topology_between_lakes(int* __restrict water, int lake_num, int* __restrict tag_array, unsigned char* __restrict dir, int rows, int cols);

int _find_next_water_body_int32(unsigned long long idx, int* __restrict water, unsigned char* __restrict dir, int cols);
int _mark_lake_outlet_int32(int* __restrict lake, int min_lake_id, int max_lake_id, unsigned char* __restrict dir, int rows, int cols);
unsigned long long* _route_between_lake(int* __restrict lake, int lake_num, unsigned char* __restrict dir, float* __restrict upa, int rows, int cols,
	int* return_num, unsigned long long* return_length);



/***********************************
 *           river part            *
 ***********************************/

int* _dfn_stream(unsigned char* __restrict dir, float* __restrict upa, float ths, int outlet_ridx, int outlet_cidx, int rows, int cols);
int _paint_river_hillslope_int32(int* __restrict stream, int min_channel_id, int max_channel_id, unsigned char* __restrict dir,
	unsigned char* __restrict re_dir, int rows, int cols);
int _check_on_mainstream(int t_ridx, int t_cidx, int inlet_ridx, int inlet_cidx, unsigned char inlet_dir, unsigned char* dir, int cols);



#endif // !_INTERFACES_H_
