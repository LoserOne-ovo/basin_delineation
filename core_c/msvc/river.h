#ifndef  _RIVER_H_
#define _RIVER_H_


int* _dfn_stream(unsigned char* __restrict dir, float* __restrict upa, float ths, int outlet_ridx, int outlet_cidx, int rows, int cols);
int _dfn_stream_overlap_lake(int* __restrict lake, unsigned char* __restrict dir, float* __restrict upa, float ths, int outlet_ridx, int outlet_cidx, int rows, int cols);

int _paint_river_hillslope_int32(int* __restrict stream, int min_channel_id, int max_channel_id, unsigned char* __restrict dir, unsigned char* __restrict re_dir, int rows, int cols);
int _decide_hillslope_id(unsigned char cur_dir, unsigned char hs_dir, unsigned char upper_stream_dir_List[], int upper_stream_num,
	int stream_id, int min_stream_id, int max_stream_id);
int _check_dir_in_upper_stream(unsigned char dir, unsigned char upper_stream_dir_List[], int upper_stream_num);

#endif // ! _RIVER_H_
