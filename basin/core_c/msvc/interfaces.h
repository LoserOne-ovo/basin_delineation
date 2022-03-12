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
int _calc_island_statistics_uint32(unsigned int* island_label, unsigned int island_num, float* center, int* sample, float* radius,
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







/***********************************
 *           sink part             *
 ***********************************/

int _dissolve_sinks_uint8(unsigned char* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
	unsigned char sink_num, int rows, int cols, double frac);

int _dissolve_sinks_uint16(unsigned short* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
	unsigned short sink_num, int rows, int cols, double frac);


#endif // !_INTERFACES_H_
