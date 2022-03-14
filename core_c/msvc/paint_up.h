#ifndef _PAINT_UP_H
#define _PAINT_UP_H

#include "list.h"


/* basin module */
int _paint_up_uint8(unsigned long long* idxs, unsigned char* colors, unsigned int idx_num, double frac,
					unsigned char* basin, unsigned char* re_dir, int rows, int cols);
int _paint_up_uint16(unsigned long long* idxs, unsigned short* colors, unsigned int idx_num, double frac,
					 unsigned short* basin, unsigned char* re_dir, int rows, int cols);
float* _calc_single_pixel_upa(unsigned char* re_dir, float* upa, int rows, int cols);


/* lake module */
int _paint_upper_int32(unsigned char* re_dir, unsigned long long idx, u64_List* stack,
	int color, int* board, const int offset[], const unsigned char div[]);
int _paint_upper_unpainted_int32(unsigned char* re_dir, unsigned long long idx, u64_List* stack,
	int color, int* board, const int offset[], const unsigned char div[]);


#endif
