#include "type_aka.h"
#include "paint_upper.h"



int _paint_upper_int32(unsigned char* re_dir, unsigned long long idx, u64_List* stack, 
	                 int color, int* board, const int offset[], const unsigned char div[]) {

	uint64 temp_idx = 0;
	uint8 reverse_fdir = 0;

	stack->List[0] = idx;
	stack->length = 1;
	
	while (stack->length > 0) {

		temp_idx = stack->List[--stack->length];
		board[temp_idx] = color;

		reverse_fdir = re_dir[temp_idx];
		for (int p = 0; p < 8; p++) {
			if (reverse_fdir >= div[p]) {
				u64_List_append(stack, temp_idx + offset[p]);
				reverse_fdir -= div[p];
			}
		}
	}
	
	return 1;
}


int _paint_upper_unpainted_int32(unsigned char* re_dir, unsigned long long idx, u64_List* stack,
	int color, int* board, const int offset[], const unsigned char div[]) {

	uint64 temp_idx = 0, upper_idx = 0;
	uint8 reverse_fdir = 0;

	stack->List[0] = idx;
	stack->length = 1;

	while (stack->length > 0) {

		temp_idx = stack->List[--stack->length];
		board[temp_idx] = color;

		reverse_fdir = re_dir[temp_idx];
		for (int p = 0; p < 8; p++) {
			if (reverse_fdir >= div[p]) {
				upper_idx = temp_idx + offset[p];
				if (board[upper_idx] == 0) {
					u64_List_append(stack, upper_idx);
				}
				reverse_fdir -= div[p];
			}
		}
	}

	return 1;
}

