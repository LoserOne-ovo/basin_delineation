#include <stdlib.h>
#include <stdio.h>
#include "paint_up.h"


int32_t _paint_up_mosaiced_uint8(uint8_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac) {

	// define variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t total_num = rows * cols64;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// initialize stack
	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	uint64_t STACK_SIZE = ((uint64_t)(total_num * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);


	// initialize outlet lsit
	u64_DynArray* outlet_idxs = u64_DynArray_Initial(STACK_SIZE);

	// look for outlets
	uint64_t idx = 0;
	for (idx = 0; idx < total_num; idx++) {
		if (basin[idx] != 0) {
			u64_DynArray_Push(outlet_idxs, idx);
		}
	}

	// assign upstream pixels of each outlet
	uint64_t outlet_num = outlet_idxs->length;
	for (uint64_t i = 0; i < outlet_num; i++) {
		idx = outlet_idxs->data[i];
		_paint_upper_unpainted_uint8(idx, basin[idx], stack, basin, re_dir, offset, div);

	}

	// free memory
	u64_DynArray_Destroy(stack);
	u64_DynArray_Destroy(outlet_idxs);
	return 1;
}

int32_t _paint_up_mosaiced_uint16(uint16_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac) {

	// define variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t total_num = rows * cols64;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// initialize stack
	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	uint64_t STACK_SIZE = ((uint64_t)(total_num * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);


	// initialize outlet lsit
	u64_DynArray* outlet_idxs = u64_DynArray_Initial(STACK_SIZE);

	// look for outlets
	uint64_t idx = 0;
	for (idx = 0; idx < total_num; idx++) {
		if (basin[idx] != 0) {
			u64_DynArray_Push(outlet_idxs, idx);
		}
	}

	// assign upstream pixels of each outlet
	uint64_t outlet_num = outlet_idxs->length;
	for (uint64_t i = 0; i < outlet_num; i++) {
		idx = outlet_idxs->data[i];
		_paint_upper_unpainted_uint16(idx, basin[idx], stack, basin, re_dir, offset, div);

	}

	// free memory
	u64_DynArray_Destroy(stack);
	u64_DynArray_Destroy(outlet_idxs);
	return 1;
}

int32_t _paint_up_mosaiced_int32(int32_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac) {

	// define variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t total_num = rows * cols64;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// initialize stack
	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	uint64_t STACK_SIZE = ((uint64_t)(total_num * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);


	// initialize outlet lsit
	u64_DynArray* outlet_idxs = u64_DynArray_Initial(STACK_SIZE);

	// look for outlets
	uint64_t idx = 0;
	for (idx = 0; idx < total_num; idx++) {
		if (basin[idx] != 0) {
			u64_DynArray_Push(outlet_idxs, idx);
		}
	}

	// assign upstream pixels of each outlet
	uint64_t outlet_num = outlet_idxs->length;
	for (uint64_t i = 0; i < outlet_num; i++) {
		idx = outlet_idxs->data[i];
		_paint_upper_unpainted_int32(idx, basin[idx], stack, basin, re_dir, offset, div);

	}

	// free memory
	u64_DynArray_Destroy(stack);
	u64_DynArray_Destroy(outlet_idxs);
	return 1;
}

int32_t _paint_up_mosaiced_uint32(uint32_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac) {

	// define variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t total_num = rows * cols64;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// initialize stack
	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	uint64_t STACK_SIZE = ((uint64_t)(total_num * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);


	// initialize outlet lsit
	u64_DynArray* outlet_idxs = u64_DynArray_Initial(STACK_SIZE);

	// look for outlets
	uint64_t idx = 0;
	for (idx = 0; idx < total_num; idx++) {
		if (basin[idx] != 0) {
			u64_DynArray_Push(outlet_idxs, idx);
		}
	}

	// assign upstream pixels of each outlet
	uint64_t outlet_num = outlet_idxs->length;
	for (uint64_t i = 0; i < outlet_num; i++) {
		idx = outlet_idxs->data[i];
		_paint_upper_unpainted_uint32(idx, basin[idx], stack, basin, re_dir, offset, div);

	}

	// free memory
	u64_DynArray_Destroy(stack);
	u64_DynArray_Destroy(outlet_idxs);
	return 1;
}


/**************************************************
 *    Assign upstream pixels of outlets with      *
 *    given values in different datatypes.        *
 **************************************************/

int32_t _paint_up_uint8(uint64_t* __restrict idxs, uint8_t* __restrict colors, uint32_t idx_num,
	uint8_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac) {

	// define variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t total_num = rows * cols64;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// initialize stack
	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	uint64_t STACK_SIZE = ((uint64_t)(total_num * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	// assign upstream pixels of each outlet
	for (uint32_t i = 0; i < idx_num; i++) {
		_paint_upper_uint8(idxs[i], colors[i], stack, basin, re_dir, offset, div);
	}

	// free memory
	u64_DynArray_Destroy(stack);
	return 1;
}

int32_t _paint_up_uint16(uint64_t* __restrict idxs, uint16_t* __restrict colors, uint32_t idx_num,
	uint16_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac) {

	// define variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t total_num = rows * cols64;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// initialize stack
	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	uint64_t STACK_SIZE = ((uint64_t)(total_num * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	// assign upstream pixels of each outlet
	for (uint32_t i = 0; i < idx_num; i++) {
		_paint_upper_uint16(idxs[i], colors[i], stack, basin, re_dir, offset, div);
	}

	// free memory
	u64_DynArray_Destroy(stack);
	return 1;
}

int32_t _paint_up_int32(uint64_t* __restrict idxs, int32_t* __restrict colors, uint32_t idx_num,
	int32_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac) {

	// define variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t total_num = rows * cols64;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// initialize stack
	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	uint64_t STACK_SIZE = ((uint64_t)(total_num * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	// assign upstream pixels of each outlet
	for (uint32_t i = 0; i < idx_num; i++) {
		_paint_upper_int32(idxs[i], colors[i], stack, basin, re_dir, offset, div);
	}

	// free memory
	u64_DynArray_Destroy(stack);
	return 1;
}

int32_t _paint_up_uint32(uint64_t* __restrict idxs, uint32_t* __restrict colors, uint32_t idx_num,
	uint32_t* __restrict basin, uint8_t* __restrict re_dir, int32_t rows, int32_t cols, double frac) {

	// define variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t total_num = rows * cols64;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// initialize stack
	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	uint64_t STACK_SIZE = ((uint64_t)(total_num * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	// assign upstream pixels of each outlet
	for (uint32_t i = 0; i < idx_num; i++) {
		_paint_upper_uint32(idxs[i], colors[i], stack, basin, re_dir, offset, div);
	}

	// free memory
	u64_DynArray_Destroy(stack);
	return 1;
}


/**************************************************
 *    Assign upstream pixels of an outlet with    *
 *    the given value in different datatypes.     *
 **************************************************/

int32_t _paint_upper_uint8(uint64_t idx, uint8_t color, u64_DynArray* stack, uint8_t* __restrict board, 
	uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]) {

	// define variables
	uint64_t temp_idx = 0;
	uint8_t reverse_fdir = 0;
	uint8_t p = 0;

	// reset stack
	stack->data[0] = idx;
	stack->length = 1;

	// iterate over upstream pixels
	while (stack->length > 0) {
		temp_idx = stack->data[--stack->length]; // pop
		board[temp_idx] = color;
		reverse_fdir = re_dir[temp_idx];
		for (p = 0; p < 8; p++) {
			if (reverse_fdir & div[p]) {
				u64_DynArray_Push(stack, temp_idx + offset[p]); // push
			}
		}
	}
	return 1;
}

int32_t _paint_upper_uint16(uint64_t idx, uint16_t color, u64_DynArray* stack, uint16_t* __restrict board, 
	uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]) {

	// define variables
	uint64_t temp_idx = 0;
	uint8_t reverse_fdir = 0;
	uint8_t p = 0;

	// reset stack
	stack->data[0] = idx;
	stack->length = 1;

	// iterate over upstream pixels
	while (stack->length > 0) {
		temp_idx = stack->data[--stack->length]; // pop
		board[temp_idx] = color;
		reverse_fdir = re_dir[temp_idx];
		for (p = 0; p < 8; p++) {
			if (reverse_fdir & div[p]) {
				u64_DynArray_Push(stack, temp_idx + offset[p]); // push
			}
		}
	}
	return 1;
}


int32_t _paint_upper_int32(uint64_t idx, int32_t color, u64_DynArray* stack, int32_t* __restrict board, 
	uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]) {

	// define variables
	uint64_t temp_idx = 0;
	uint8_t reverse_fdir = 0;
	uint8_t p = 0;

	// reset stack
	stack->data[0] = idx;
	stack->length = 1;

	// iterate over upstream pixels
	while (stack->length > 0) {
		temp_idx = stack->data[--stack->length]; // pop
		board[temp_idx] = color;
		reverse_fdir = re_dir[temp_idx];
		for (p = 0; p < 8; p++) {
			if (reverse_fdir & div[p]) {
				u64_DynArray_Push(stack, temp_idx + offset[p]); // push
			}
		}
	}
	return 1;
}


int32_t _paint_upper_uint32(uint64_t idx, uint32_t color, u64_DynArray* stack, uint32_t* __restrict board, 
	uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]) {

	// define variables
	uint64_t temp_idx = 0;
	uint8_t reverse_fdir = 0;
	uint8_t p = 0;

	// reset stack
	stack->data[0] = idx;
	stack->length = 1;

	// iterate over upstream pixels
	while (stack->length > 0) {
		temp_idx = stack->data[--stack->length]; // pop
		board[temp_idx] = color;
		reverse_fdir = re_dir[temp_idx];
		for (p = 0; p < 8; p++) {
			if (reverse_fdir & div[p]) {
				u64_DynArray_Push(stack, temp_idx + offset[p]); // push
			}
		}
	}
	return 1;
}


 /**************************************************
  *    Assign (non-value) upstream pixels of an    *
  *    outlet with the given value in different    *
  *    datatypes.                                  *
  **************************************************/

int32_t _paint_upper_unpainted_uint8(uint64_t idx, uint8_t color, u64_DynArray* stack, uint8_t* __restrict board,
	uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]) {
	
	// define variables
	uint64_t temp_idx = 0, upper_idx = 0;
	uint8_t reverse_fdir = 0;
	uint8_t p = 0;
	
	// reset stack
	stack->data[0] = idx;
	stack->length = 1;

	// iterate over upstream pixels
	while (stack->length > 0) {
		temp_idx = stack->data[--stack->length];
		board[temp_idx] = color;
		reverse_fdir = re_dir[temp_idx];
		for (p = 0; p < 8; p++) {
			if (reverse_fdir & div[p]) {
				upper_idx = temp_idx + offset[p];
				// find unpainted upstream pixels
				if (board[upper_idx] == 0) {
					u64_DynArray_Push(stack, upper_idx);
				}
			}
		}
	}
	return 1;
}

int32_t _paint_upper_unpainted_uint16(uint64_t idx, uint16_t color, u64_DynArray* stack, uint16_t* __restrict board,
	uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]) {

	// define variables
	uint64_t temp_idx = 0, upper_idx = 0;
	uint8_t reverse_fdir = 0;
	uint8_t p = 0;

	// reset stack
	stack->data[0] = idx;
	stack->length = 1;

	// iterate over upstream pixels
	while (stack->length > 0) {
		temp_idx = stack->data[--stack->length];
		board[temp_idx] = color;
		reverse_fdir = re_dir[temp_idx];
		for (p = 0; p < 8; p++) {
			if (reverse_fdir & div[p]) {
				upper_idx = temp_idx + offset[p];
				// find unpainted upstream pixels
				if (board[upper_idx] == 0) {
					u64_DynArray_Push(stack, upper_idx);
				}
			}
		}
	}
	return 1;
}

int32_t _paint_upper_unpainted_int32(uint64_t idx, int32_t color, u64_DynArray* stack, int32_t* __restrict board,
	uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]) {

	// define variables
	uint64_t temp_idx = 0, upper_idx = 0;
	uint8_t reverse_fdir = 0;
	uint8_t p = 0;

	// reset stack
	stack->data[0] = idx;
	stack->length = 1;

	// iterate over upstream pixels
	while (stack->length > 0) {
		temp_idx = stack->data[--stack->length];
		board[temp_idx] = color;
		reverse_fdir = re_dir[temp_idx];
		for (p = 0; p < 8; p++) {
			if (reverse_fdir & div[p]) {
				upper_idx = temp_idx + offset[p];
				// find unpainted upstream pixels
				if (board[upper_idx] == 0) {
					u64_DynArray_Push(stack, upper_idx);
				}
			}
		}
	}
	return 1;
}

int32_t _paint_upper_unpainted_uint32(uint64_t idx, uint32_t color, u64_DynArray* stack, uint32_t* __restrict board,
	uint8_t* __restrict re_dir, const int32_t offset[], const uint8_t div[]) {

	// define variables
	uint64_t temp_idx = 0, upper_idx = 0;
	uint8_t reverse_fdir = 0;
	uint8_t p = 0;

	// reset stack
	stack->data[0] = idx;
	stack->length = 1;

	// iterate over upstream pixels
	while (stack->length > 0) {
		temp_idx = stack->data[--stack->length];
		board[temp_idx] = color;
		reverse_fdir = re_dir[temp_idx];
		for (p = 0; p < 8; p++) {
			if (reverse_fdir & div[p]) {
				upper_idx = temp_idx + offset[p];
				// find unpainted upstream pixels
				if (board[upper_idx] == 0) {
					u64_DynArray_Push(stack, upper_idx);
				}
			}
		}
	}
	return 1;
}


//// 反推每个栅格的汇流累积量
//float* _calc_single_pixel_upa(uint8_t* __restrict re_dir, float* __restrict upa, int32_t rows, int32_t cols) {
//
//	// 初始化辅助参数
//	uint64_t idx = 0;
//	uint64_t total_num = rows * (uint64_t)cols;
//	uint8_t reverse_fdir = 0;
//	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
//	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
//	float temp_upa = 0.f;
//	int32_t np = 0;
//
//	// 初始化返回结果
//	float* __restrict result = (float*)malloc(total_num * sizeof(float));
//	if (result == NULL) {
//		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
//		exit(-1);
//	}
//	for (idx = 0; idx < total_num; idx++) {
//		temp_upa = upa[idx];
//		// 如果该栅格有汇流累积量，计算该栅格本身对汇流累积量的贡献
//		// 方法是用该栅格的汇流累积量，减去所有直接上游的汇流累积量
//		if (temp_upa != -9999.f) {
//			reverse_fdir = re_dir[idx];
//			for (np = 0; np < 8; np++) {
//				if (reverse_fdir >= div[np]) {
//					temp_upa -= upa[idx + offset[np]];
//					reverse_fdir -= div[np];
//				}
//			}
//			result[idx] = temp_upa;
//		}
//		else {
//			result[idx] = -9999.f;
//		}
//	}
//	return result;
//}


