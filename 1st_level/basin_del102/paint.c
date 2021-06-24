#include "paint.h"

int paint(unsigned char* re_fdir, unsigned short* basin, unsigned long long idx, unsigned short color, const unsigned char div[], const int offset[]) {


	basin[idx] = color;
	unsigned char reverse_fdir = re_fdir[idx];

	for (int i = 0; i < 8; i++) {
		if (reverse_fdir >= div[i]) {
			paint(re_fdir, basin, idx + offset[i], color, div, offset);
			reverse_fdir -= div[i];
		}
	}

	return 1;
}