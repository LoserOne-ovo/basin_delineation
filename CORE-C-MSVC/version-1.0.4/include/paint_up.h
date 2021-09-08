#ifndef _PAINT_UP_H
#define _PAINT_UP_H

int _paint_up_uint8(unsigned long long* idxs, unsigned char* colors, unsigned int idx_num, double frac,
					unsigned char* basin, unsigned char* re_dir, int rows, int cols);
int _paint_up_uint16(unsigned long long* idxs, unsigned short* colors, unsigned int idx_num, double frac, \
	unsigned short* basin, unsigned char* re_dir, int rows, int cols);

#endif
