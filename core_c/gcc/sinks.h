#ifndef _PAINT_UP_INNER_H_
#define _PAINT_UP_INNER_H_

#include "list.h"


int _dissolve_sinks_uint16(unsigned short* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
						   unsigned short sink_num, int rows, int cols, double frac);
unsigned short* _inner_merge_u16(unsigned short* basin, float* elev, u64_List* rim_cell, 
								 unsigned short sink_num, unsigned short min_sink, const int offset[]);
u64_List* _remove_inner_peak_u16(u64_List* src, unsigned short* basin, u16_List* cur_color, const int offset[]);
u64_List* _eL_merge_u16(u64_List* src, u64_List* ins, unsigned short* basin, u16_List* cur_basin, const int offset[]);
unsigned short _find_next_basin_u16(u64_List* edge_list, float* elev, unsigned short* basin, u16_List* cur_basin, const int offset[]);


int _dissolve_sinks_uint8(unsigned char* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
						  unsigned char sink_num, int rows, int cols, double frac);
unsigned char* _inner_merge_u8(unsigned char* basin, float* elev, u64_List* rim_cell,
							   unsigned char sink_num, unsigned char min_sink, const int offset[]);
u64_List* _remove_inner_peak_u8(u64_List* src, unsigned char* basin, u8_List* cur_color, const int offset[]);
u64_List* _eL_merge_u8(u64_List* src, u64_List* ins, unsigned char* basin, u8_List* cur_basin, const int offset[]);
unsigned char _find_next_basin_u8(u64_List* edge_list, float* elev, unsigned char* basin, u8_List* cur_basin, const int offset[]);


#endif
