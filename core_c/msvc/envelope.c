#include <stdlib.h>
#include <stdio.h>
#include "envelope.h"


int32_t _get_basin_envelope_uint8(uint8_t* __restrict basin, int32_t* envelopes, int32_t rows, int32_t cols) {

	uint64_t idx = 0;
	uint8_t basin_code = 0;
	uint8_t tuple_probe = 0;

	for (int32_t i = 0; i < rows; i++) {
		for (int32_t j = 0; j < cols; j++) {

			basin_code = basin[idx];
			if (basin_code != 0) {
				tuple_probe = 4 * basin_code;
				if (i < envelopes[tuple_probe]) {
					envelopes[tuple_probe] = i;
				}
				if (i > envelopes[tuple_probe + 2]) {
					envelopes[tuple_probe + 2] = i;
				}

				if (j < envelopes[tuple_probe + 1]) {
					envelopes[tuple_probe + 1] = j;
				}
				if (j > envelopes[tuple_probe + 3]) {
					envelopes[tuple_probe + 3] = j;
				}
			}
			++idx;
		}
	}

	return 1;
}


int32_t _get_basin_envelope_int32(int32_t* __restrict basin, int32_t* envelopes, int32_t rows, int32_t cols) {

	uint64_t idx = 0;
	int32_t basin_code = 0;
	int32_t tuple_probe = 0;

	for (int32_t i = 0; i < rows; i++) {
		for (int32_t j = 0; j < cols; j++) {

			basin_code = basin[idx];
			if (basin_code != 0) {
				tuple_probe = 4 * basin_code;
				if (i < envelopes[tuple_probe]) {
					envelopes[tuple_probe] = i;
				}
				if (i > envelopes[tuple_probe + 2]) {
					envelopes[tuple_probe + 2] = i;
				}

				if (j < envelopes[tuple_probe + 1]) {
					envelopes[tuple_probe + 1] = j;
				}
				if (j > envelopes[tuple_probe + 3]) {
					envelopes[tuple_probe + 3] = j;
				}
			}
			++idx;
		}
	}

	return 1;
}
