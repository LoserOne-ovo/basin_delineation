#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "interfaces.h"



__declspec(dllexport) unsigned int* label_4con(unsigned char* bin_ima, int rows, int cols, unsigned int* label_num) {

	return _label_4con(bin_ima, rows, cols, label_num);
}




__declspec(dllexport) unsigned char* calc_reverse_fdir(unsigned char* fdir, int rows, int cols) {
	
	return _get_re_dir(fdir, rows, cols);

}




__declspec(dllexport) int paint_up_mosaiced_uint16(unsigned int* ridx, unsigned int* cidx, unsigned int num, int rows, int cols, 
	                                        double frac, unsigned char* re_dir, unsigned short* basin){

	uint64 cols64 = (uint64)cols;
	uint64* idxs_1D = (uint64*)calloc(num, sizeof(unsigned long long));
	if (idxs_1D == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint i = 0; i < num; i++) {
		idxs_1D[i] = ridx[i] * cols64 + cidx[i];
	}
	
	uint16* colors = (uint16*)calloc(num, sizeof(unsigned short));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint i = 0; i < num; i++) {
		colors[i] = basin[idxs_1D[i]];
	}

	int result = _paint_up_uint16(idxs_1D, colors, num, frac, basin, re_dir, rows, cols);

	return result;
	
}




__declspec(dllexport) int paint_up_mosaiced_uint8(unsigned int* ridx, unsigned int* cidx, unsigned int num, int rows, int cols,
	double frac, unsigned char* re_dir, unsigned char* basin) {

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

	return _paint_up_uint8(idxs_1D, colors, num, frac, basin, re_dir, rows, cols);

}




__declspec(dllexport) unsigned long long* calc_gc(unsigned int* label_res, unsigned int label_num, int rows, int cols)
{
	return _calc_geometry_center(label_res, label_num, rows, cols);
}




__declspec(dllexport) int islands_merge(unsigned int* label_res, unsigned char* basin, unsigned int label_num,
	int rows, int cols, unsigned char* colors)
{

	uint64 total = rows * (uint64)cols;
	register uint64 idx = 0;

	for (idx = 0; idx < total; idx++) {
		if (label_res[idx] != 0) {
			basin[idx] = colors[label_res[idx] - 1];
		}
	}

	return 1;
}




__declspec(dllexport) int dissolve_sinks_uint16(unsigned int* ridx, unsigned int* cidx, unsigned short sink_num, int rows, int cols, 
	double frac, unsigned char* re_dir, unsigned short* basin, float* dem) {

	
	register uint64 cols64 = (uint64)cols;
	uint64 stack_size = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (stack_size > 100000000) {
		stack_size = 100000000;
	}

	// 初始化一维位置索引
	uint64* sink_idxs = (uint64*)calloc(sink_num, sizeof(unsigned long long));
	if (sink_idxs == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint16 i = 0; i < sink_num; i++) {
		sink_idxs[i] = ridx[i] * cols64 + cidx[i];
	}

	// 初始化颜色设置
	uint16 min_sink = 11;
	uint16* colors = (uint16*)calloc(sink_num, sizeof(unsigned short));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint16 i = 0; i < sink_num; i++) {
		colors[i] = min_sink + i;
	}

	return _dissolve_sinks_uint16(basin, re_dir, dem, sink_idxs, colors, sink_num, min_sink, cols, stack_size);

}




__declspec(dllexport) int dissolve_sinks_uint8(unsigned int* ridx, unsigned int* cidx, unsigned char sink_num,int rows, int cols,
	double frac, unsigned char* re_dir, unsigned char* basin, float* dem)
{

	register uint64 cols64 = (uint64)cols;
	uint64 stack_size = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (stack_size > 100000000) {
		stack_size = 100000000;
	}

	// 初始化一维位置索引
	uint64* sink_idxs = (uint64*)calloc(sink_num, sizeof(unsigned long long));
	if (sink_idxs == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint8 i = 0; i < sink_num; i++) {
		sink_idxs[i] = ridx[i] * cols64 + cidx[i];
	}

	// 初始化颜色设置
	uint8 min_sink = 11;
	uint8* colors = (uint8*)calloc(sink_num, sizeof(unsigned char));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint8 i = 0; i < sink_num; i++) {
		colors[i] = min_sink + i;
	}

	return _dissolve_sinks_uint8(basin, re_dir, dem, sink_idxs, colors, sink_num, min_sink, cols, stack_size);

}




__declspec(dllexport) unsigned char* pfafstetter(unsigned int outlet_ridx, unsigned int outlet_cidx, unsigned char* re_dir, 
	float* upa, int rows, int cols, float ths, unsigned int* r_ridxs, unsigned int* r_cidxs, unsigned char* return_num) {

	uint64 outlet_idx = outlet_ridx * (uint64)cols + outlet_cidx;
	return _pfs_r_uint8(re_dir, upa, rows, cols, ths, outlet_idx, r_ridxs, r_cidxs, return_num);

}




__declspec(dllexport) int paint_up_uint8(unsigned int* ridx, unsigned int* cidx, unsigned char* colors, 
	unsigned int num, int rows, int cols, double frac, unsigned char* re_dir, unsigned char* basin) {

	// 将二维索引转换为1维索引
	uint64 cols64 = (uint64)cols;
	uint64* idxs_1D = (uint64*)calloc(num, sizeof(unsigned long long));
	if (idxs_1D == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint i = 0; i < num; i++) {
		idxs_1D[i] = ridx[i] * cols64 + cidx[i];
	}

	return _paint_up_uint8(idxs_1D, colors, num, frac, basin, re_dir, rows, cols);
}




__declspec(dllexport) unsigned short* dissolve_basin(unsigned int outlet_ridx, unsigned int outlet_cidx, float ths,
													 unsigned int* sink_ridxs, unsigned int* sink_cidxs, unsigned short sink_num,
													 unsigned char* dir, float* upa, float* dem, int rows, int cols) {

	uint64 cols64 = (uint64)cols;
	uint64 outlet_idx = outlet_ridx * cols64 + outlet_cidx;
	uint64* sink_idxs = (uint64*)calloc(sink_num, sizeof(unsigned long long));
	if (sink_idxs == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint16 i = 0; i < sink_num; i++) {
		sink_idxs[i] = sink_ridxs[i] * cols64 + sink_cidxs[i];
	}

	return _dissolve_basin(dir, upa, dem, rows, cols, ths, outlet_idx, sink_idxs, sink_num);
}



__declspec(dllexport) unsigned char* track_all_basins(unsigned char* dir, int rows, int cols) {

	return _track_all_basins(dir, rows, cols);
}

