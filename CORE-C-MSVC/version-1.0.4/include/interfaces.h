#ifndef _INTERFACES_H_
#define _INTERFACES_H_


unsigned short* _dissolve_basin(unsigned char* dir, float* upa, float* dem, int rows, int cols, float ths,
								unsigned long long outlet_idx, unsigned long long* sink_idxs, unsigned short sink_num);

unsigned int* _label_4con(unsigned char* bin_ima, int rows, int cols, unsigned int* label_num);

unsigned char* _get_re_dir(unsigned char* fdir, int rows, int cols);

unsigned long long* _calc_geometry_center(unsigned int* label_res, unsigned int label_num, int rows, int cols);

int _paint_up_uint16(unsigned long long* idxs, unsigned short* colors, unsigned int idx_num, double frac,
					 unsigned short* basin, unsigned char* re_dir, int rows, int cols);

int _paint_up_uint8(unsigned long long* idxs, unsigned char* colors, unsigned int idx_num,
					double frac, unsigned char* basin, unsigned char* re_dir, int rows, int cols);

int _dissolve_sinks_uint16(unsigned short* basin, unsigned char* re_dir, float* dem,
					unsigned long long* sink_idxs, unsigned short* colors, unsigned short sink_num,
					unsigned short min_sink, int cols, unsigned long long QUENE_SIZE);


int _dissolve_sinks_uint8(unsigned char* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
	unsigned char* colors, unsigned char sink_num, unsigned char min_sink, int cols, unsigned long long QUENE_SIZE);


unsigned char* _pfs_r_uint8(unsigned char* re_dir, float* upa, int rows, int cols, float ths,
							unsigned long long outlet_idx, unsigned int* r_ridxs, unsigned int* r_cidxs, unsigned char* r_num);

int _paint_up_uint8(unsigned long long* idxs, unsigned char* colors, unsigned int idx_num, double frac,
	unsigned char* basin, unsigned char* re_dir, int rows, int cols);

unsigned char* _track_all_basins(unsigned char* dir, int rows, int cols);


#endif // !_INTERFACES_H_
