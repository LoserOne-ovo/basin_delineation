#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "paint_up.h"
#include "list.h"


// unsigned char数据类型的出水口上游绘制
int _paint_up_uint8(unsigned long long* idxs, unsigned char* colors, unsigned int idx_num, double frac,
	unsigned char* basin, unsigned char* re_dir, int rows, int cols) {

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
int _paint_up_uint16(unsigned long long* idxs, unsigned short* colors, unsigned int idx_num, double frac,
					 unsigned short* basin, unsigned char* re_dir, int rows, int cols) {

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
