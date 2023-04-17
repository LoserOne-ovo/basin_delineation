#ifndef _ENVELOPES_H_
#define _ENVELOPES_H_

#include <stdint.h>


int32_t _get_basin_envelope_uint8(uint8_t* __restrict basin, int32_t* envelopes, int32_t rows, int32_t cols);
int32_t _get_basin_envelope_int32(int32_t* __restrict basin, int32_t* envelopes, int32_t rows, int32_t cols);


#endif
