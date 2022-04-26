#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "list.h"


/*********************************
 *    流域模块。                 *
 *	  各个上游都是互相独立的。   *
 *********************************/


// unsigned char数据类型的出水口上游绘制
int _paint_up_uint8(unsigned long long* __restrict idxs, unsigned char* __restrict colors, unsigned int idx_num, double frac,
	unsigned char* __restrict basin, unsigned char* __restrict re_dir, int rows, int cols) {

	uint64 cols64 = (uint64)cols;
	// 根据提供的比例，计算需要用到的栈深度
	uint64 STACK_SIZE = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}

	// 初始化
	uint64 idx = 0;
	uint8 reverse_fdir = 0;
	uint8 color = 0;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_List stack = { 0,0,STACK_SIZE,NULL };
	stack.List = (uint64*)calloc(STACK_SIZE, sizeof(uint64));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = STACK_SIZE;

	// 逐一绘制上游，后绘制的会覆盖先前的绘制结果，所以需要注意输入索引的顺序
	for (uint i = 0; i < idx_num; i++) {
		idx = idxs[i];
		color = colors[i];

		// 重置栈
		stack.List[0] = idx;
		stack.length = 1;

		while (stack.length > 0) {
			// 出栈上色
			idx = stack.List[stack.length - 1];
			stack.length--;
			basin[idx] = color;
			// 上游入栈
			reverse_fdir = re_dir[idx];
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_List_append(&stack, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
		}
	}

	// 释放内存
	free(stack.List);
	stack.List = NULL;
	stack.length = 0;
	stack.batch_size = 0;
	stack.alloc_length = 0;

	return 1;
}


// unsigned short数据类型的出水口上游绘制
int _paint_up_uint16(unsigned long long* __restrict idxs, unsigned short* __restrict colors, unsigned int idx_num, double frac,
					 unsigned short* __restrict basin, unsigned char* __restrict re_dir, int rows, int cols) {

	uint64 cols64 = (uint64)cols;
	// 根据提供的比例，计算需要用到的栈深度
	uint64 STACK_SIZE = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}

	// 初始化
	uint64 idx = 0;
	uint8 reverse_fdir = 0;
	uint16 color;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_List stack = { 0,0,STACK_SIZE,NULL };
	stack.List = (uint64*)calloc(STACK_SIZE, sizeof(uint64));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = STACK_SIZE;

	// 逐一绘制上游，后绘制的会覆盖先前的绘制结果，所以需要注意输入索引的顺序
	for (uint i = 0; i < idx_num; i++) {

		idx = idxs[i];
		color = colors[i];

		// 重置栈
		stack.List[0] = idx;
		stack.length = 1;

		while (stack.length > 0) {
			// 出栈上色
			idx = stack.List[stack.length - 1];
			stack.length--;
			basin[idx] = color;
			// 上游入栈
			reverse_fdir = re_dir[idx];
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_List_append(&stack, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
		}
	}

	// 释放内存
	free(stack.List);
	stack.List = NULL;
	stack.length = 0;
	stack.batch_size = 0;
	stack.alloc_length = 0;

	return 1;
}


int _paint_up_uint32(unsigned long long* __restrict idxs, 
					 unsigned int* __restrict colors, 
					 unsigned int idx_num, double frac,
					 unsigned int* __restrict basin, 
				     unsigned char* __restrict re_dir, 
					 int rows, int cols) {

	uint64 cols64 = (uint64)cols;
	// 根据提供的比例，计算需要用到的栈深度
	uint64 STACK_SIZE = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}

	// 初始化
	uint64 idx = 0;
	uint8 reverse_fdir = 0;
	uint color = 0;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_List stack = { 0,0,STACK_SIZE,NULL };
	stack.List = (uint64*)calloc(STACK_SIZE, sizeof(uint64));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = STACK_SIZE;

	// 逐一绘制上游，后绘制的会覆盖先前的绘制结果，所以需要注意输入索引的顺序
	for (uint i = 0; i < idx_num; i++) {
		idx = idxs[i];
		color = colors[i];

		// 重置栈
		stack.List[0] = idx;
		stack.length = 1;

		while (stack.length > 0) {
			// 出栈上色
			idx = stack.List[stack.length - 1];
			stack.length--;
			basin[idx] = color;
			// 上游入栈
			reverse_fdir = re_dir[idx];
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_List_append(&stack, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
		}
	}

	// 释放内存
	free(stack.List);
	stack.List = NULL;
	stack.length = 0;
	stack.batch_size = 0;
	stack.alloc_length = 0;

	return 1;
}




// 反推每个栅格的汇流累积量
float* _calc_single_pixel_upa(unsigned char* __restrict re_dir, float* __restrict upa, int rows, int cols) {

	// 初始化辅助参数
	uint64 idx = 0;
	uint64 total_num = rows * (uint64)cols;
	uint8 reverse_fdir = 0;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	float temp_upa = 0.f;
	int np = 0;

	// 初始化返回结果
	float* __restrict result = (float*)malloc(total_num * sizeof(float));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	

	for (idx = 0; idx < total_num; idx++) {
		temp_upa = upa[idx];
		// 如果该栅格有汇流累积量，计算该栅格本身对汇流累积量的贡献
		// 方法是用该栅格的汇流累积量，减去所有直接上游的汇流累积量
		if (temp_upa != -9999.f) {
			reverse_fdir = re_dir[idx];
			for (np = 0; np < 8; np++) {
				if (reverse_fdir >= div[np]) {
					temp_upa -= upa[idx + offset[np]];
					reverse_fdir -= div[np];
				}
			}
			result[idx] = temp_upa;
		}
		else {
			result[idx] = -9999.f;
		}
	}	

	return result;
}





/*********************************
 *    湖泊模块。                 *
 *	  各个上游不是互相独立的。   *
 *    与流域模块封装尺度不同。   *
 *********************************/


int _paint_upper_int32(unsigned char* __restrict re_dir, unsigned long long idx, u64_List* stack,
	int color, int* __restrict board, const int offset[], const unsigned char div[]) {

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


int _paint_upper_unpainted_int32(unsigned char* __restrict re_dir, unsigned long long idx, u64_List* stack,
	int color, int* __restrict board, const int offset[], const unsigned char div[]) {

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






