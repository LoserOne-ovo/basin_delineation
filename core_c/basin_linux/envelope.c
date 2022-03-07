#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"



int _get_basin_envelope_uint8(unsigned char* basin, int* envelopes, int rows, int cols) {

	uint64 idx = 0;
	uint8 basin_code = 0;
	uint8 tuple_probe = 0;

	for (int i = 0; i < rows; i++) {
		for (int j = 0; j < cols; j++) {

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