#ifndef _PAINT_UP_H
#define _PAINT_UP_H

#include "list.h"


/* basin module */
int _paint_up_uint8(unsigned long long* __restrict idxs, unsigned char* __restrict colors, unsigned int idx_num, double frac,
					unsigned char* __restrict basin, unsigned char* __restrict re_dir, int rows, int cols);
int _paint_up_uint16(unsigned long long* __restrict idxs, unsigned short* __restrict colors, unsigned int idx_num, double frac,
					 unsigned short* __restrict basin, unsigned char* __restrict re_dir, int rows, int cols);
int _paint_up_uint32(unsigned long long* __restrict idxs, unsigned int* __restrict colors, unsigned int idx_num, double frac,
	unsigned int* __restrict basin, unsigned char* __restrict re_dir, int rows, int cols);
float* _calc_single_pixel_upa(unsigned char* __restrict re_dir, float* __restrict upa, int rows, int cols);


/* lake module */
int _paint_upper_int32(unsigned char* __restrict re_dir, unsigned long long idx, u64_List* stack,
	int color, int* __restrict board, const int offset[], const unsigned char div[]);
int _paint_upper_unpainted_int32(unsigned char* __restrict re_dir, unsigned long long idx, u64_List* stack,
	int color, int* __restrict board, const int offset[], const unsigned char div[]);


#endif
