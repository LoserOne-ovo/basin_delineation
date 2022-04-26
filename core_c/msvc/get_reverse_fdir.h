#ifndef _GET_REVERSE_FDIR_H_
#define _GET_REVERSE_FDIR_H_

unsigned char* _get_re_dir(unsigned char* __restrict fdir, int rows, int cols);
unsigned int _get_down_idx32(unsigned char loc_dir, unsigned int idx, int cols);
unsigned long long _get_down_idx64(unsigned char loc_dir, unsigned long long idx, int cols);
unsigned char _get_up_dir(unsigned char upper_dir);
unsigned char _get_next_dir_clockwise(unsigned char dir);








#endif // !_GET_REVERSE_FDIR_H_
