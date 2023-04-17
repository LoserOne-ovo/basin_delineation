#ifndef _GET_REVERSE_FDIR_H_
#define _GET_REVERSE_FDIR_H_

#include <stdint.h>


uint8_t* _get_re_dir(uint8_t* __restrict fdir, int32_t rows, int32_t cols);
uint32_t _get_down_idx32(uint8_t loc_dir, uint32_t idx, int32_t cols);
uint64_t _get_down_idx64(uint8_t loc_dir, uint64_t idx, int32_t cols);
uint8_t _get_up_dir(uint8_t upper_dir);
uint8_t _get_next_dir_clockwise(uint8_t dir);

#endif // !_GET_REVERSE_FDIR_H_
