#ifndef _PAINT_UP_INNER_H_
#define _PAINT_UP_INNER_H_

#include "list.h"


const unsigned int S_SIZE = 100;
const unsigned int M_SIZE = 1000;
const unsigned int L_SIZE = 10000;
const unsigned int XL_SIZE = 100000;
const unsigned int SL_SIZE = 1000000;
const unsigned int ML_SIZE = 10000000;
const unsigned int LL_SIZE = 100000000;


unsigned short* inner_merge(int inner_num, int outer_num, u64_List* rim_cell, unsigned short* basin, float* elev, const int offset[]);
u64_List* remove_inner_peak(u64_List* src, unsigned short* basin, u16_List* cur_color, const int offset[]);
unsigned short find_next_basin(u64_List* edge_list, float* elev, unsigned short* basin, u16_List* cur_basin, const int offset[]);
u64_List* eL_merge(u64_List* src, u64_List* ins, unsigned short* basin, u16_List* cur_color, const int offset[]);


#endif
