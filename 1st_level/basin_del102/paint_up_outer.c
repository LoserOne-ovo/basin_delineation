#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "paint.h"

__declspec(dllexport) int paint_up(unsigned int* ridx, unsigned int* cidx, int cols, 
								   unsigned int num, unsigned char* re_fdir, unsigned short* basin) 
{

	uint64 cols64 = (uint64)cols;
	uint64 idx = 0;
	uint8 reverse_fdir = 0;
	uint16 color = 0;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	for (uint i = 0; i < num; i++) {

		idx = ridx[i] * cols64 + cidx[i];
		color = basin[idx];
		paint(re_fdir, basin, idx, color, div, offset);

	}

	return 1;
}
