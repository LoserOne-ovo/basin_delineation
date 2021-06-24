#ifndef _PAINT_UP_INNER_H_
#define _PAINT_UP_INNER_H_

#include "list.h"


const unsigned int S_SIZE = 100;
const unsigned int M_SIZE = 1000;
const unsigned int L_SIZE = 10000;
const unsigned int XL_SIZE = 100000;
const unsigned int XXL_SIZE = 1000000;
const unsigned int XXXL_SIZE = 10000000;


unsigned short* inner_merge(int inner_num, int outer_num, u64_List* rim_cell, unsigned short* basin, float* elev, const int offset[]);
u64_List* remove_inner_peak(u64_List* src, unsigned short* basin, u16_List* cur_color, const int offset[]);
unsigned short find_next_basin(u64_List* edge_list, float* elev, unsigned short* basin, u16_List* cur_basin, const int offset[]);
u64_List* eL_merge(u64_List* src, u64_List* ins, unsigned short* basin, u16_List* cur_color, const int offset[]);
int paint_rc(unsigned char* re_fdir, unsigned short* basin, u64_List* rim_cell_i, unsigned long long idx, unsigned short color, const unsigned char div[], const int offset[]);


#endif
