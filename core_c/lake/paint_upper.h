#ifndef _PAINT_UPPER_H_
#define _PAINT_UPPER_H_

#include "list.h"

int _paint_upper_int32(unsigned char* re_dir, unsigned long long idx, u64_List* stack,
					 int color, int* board, const int offset[], const unsigned char div[]);
int _paint_upper_unpainted_int32(unsigned char* re_dir, unsigned long long idx, u64_List* stack,
	int color, int* board, const int offset[], const unsigned char div[]);


#endif // !_PAINT_UPPER_H_
