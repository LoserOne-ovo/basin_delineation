#ifndef  _RIVER_H_
#define _RIVER_H_

#include <stdint.h>



int32_t* _dfn_stream(uint8_t* __restrict dir, float* __restrict upa, float ths, int32_t outlet_ridx, int32_t outlet_cidx, int32_t rows, int32_t cols);
int32_t _dfn_stream_overlap_lake(int32_t* __restrict lake, uint8_t* __restrict dir, float* __restrict upa, float ths, int32_t outlet_ridx, int32_t outlet_cidx, int32_t rows, int32_t cols);

int32_t _paint_river_hillslope_int32(int32_t* __restrict stream, int32_t min_channel_id, int32_t max_channel_id, uint8_t* __restrict dir, uint8_t* __restrict re_dir, int32_t rows, int32_t cols);
int32_t _decide_hillslope_id(uint8_t cur_dir, uint8_t hs_dir, uint8_t upper_stream_dir_List[], int32_t upper_stream_num,
	int32_t stream_id, int32_t min_stream_id, int32_t max_stream_id);
int32_t _check_dir_in_upper_stream(uint8_t dir, uint8_t upper_stream_dir_List[], int32_t upper_stream_num);


uint8_t _dertermine_hillslope_postition(uint8_t cur_dir, uint8_t hs_dir, uint8_t upper_stream_dir);

#endif // ! _RIVER_H_
