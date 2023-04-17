#ifndef _PAINT_UP_H
#define _PAINT_UP_H

#include "Array.h"


int32_t _paint_up_mosaiced_uint8(uint8_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac);
int32_t _paint_up_mosaiced_uint16(uint16_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac);
int32_t _paint_up_mosaiced_int32(int32_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac);
int32_t _paint_up_mosaiced_uint32(uint32_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac);

int32_t _paint_up_uint8(uint64_t* __restrict idxs, uint8_t* __restrict colors, uint32_t idx_num, uint8_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac);
int32_t _paint_up_uint16(uint64_t* __restrict idxs, uint16_t* __restrict colors, uint32_t idx_num, uint16_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac);
int32_t _paint_up_int32(uint64_t* __restrict idxs, int32_t* __restrict colors, uint32_t idx_num, int32_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac);
int32_t _paint_up_uint32(uint64_t* __restrict idxs, uint32_t* __restrict colors, uint32_t idx_num, uint32_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac);

int32_t _paint_upper_uint8(uint64_t idx, uint8_t color, u64_DynArray* stack, uint8_t* __restrict board, uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]);
int32_t _paint_upper_uint16(uint64_t idx, uint16_t color, u64_DynArray* stack, uint16_t* __restrict board, uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]);
int32_t _paint_upper_int32(uint64_t idx, int32_t color, u64_DynArray* stack, int32_t* __restrict board, uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]);
int32_t _paint_upper_uint32(uint64_t idx, uint32_t color, u64_DynArray* stack, uint32_t* __restrict board, uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]);

int32_t _paint_upper_unpainted_uint8(uint64_t idx, uint8_t color, u64_DynArray* stack, uint8_t* __restrict board, uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]);
int32_t _paint_upper_unpainted_uint16(uint64_t idx, uint16_t color, u64_DynArray* stack, uint16_t* __restrict board, uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]);
int32_t _paint_upper_unpainted_int32(uint64_t idx, int32_t color, u64_DynArray* stack, int32_t* __restrict board, uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]);
int32_t _paint_upper_unpainted_uint32(uint64_t idx, uint32_t color, u64_DynArray* stack, uint32_t* __restrict board, uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]);


//float* _calc_single_pixel_upa(uint8_t* __restrict re_dir, float* __restrict upa, int32_t rows, int32_t cols);


#endif
