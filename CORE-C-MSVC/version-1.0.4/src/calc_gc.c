#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "list.h"
#include "calc_gc.h"

/// <summary>
///	计算岛屿边界的几何中心，以便查找最近的外流流域
/// </summary>
/// <param name="label_res"></param>
/// <param name="label_num"></param>
/// <param name="rows"></param>
/// <param name="cols"></param>
/// <returns></returns>
unsigned long long* _calc_geometry_center(unsigned int* label_res, unsigned int label_num, int rows, int cols) {

	register uint64 cols64 = (uint64)cols;
	register uint64 total = rows * cols64;
	register uint64 idx = 0;
	uint64 EL_SIZE = 1000;


	// 初始化列表
	u64_List* eList = (u64_List*)malloc(label_num * sizeof(u64_List));
	if (eList == NULL) {
		fprintf(stderr, "memory allocation failed in line %d of calc_gc.c \r\n", __LINE__);
		exit(-1);
	}

	for (uint i = 0; i < label_num; i++) {
		eList[i].length = 0;
		eList[i].batch_size = EL_SIZE;
		eList[i].List = (uint64*)calloc(EL_SIZE, sizeof(uint64));
		if (eList[i].List == NULL) {
			fprintf(stderr, "memory allocation failed in line %d of calc_gc.c \r\n", __LINE__);
			exit(-1);
		}
		eList[i].alloc_length = EL_SIZE;

	}

	// 向列表中添加元素
	for (idx = 0; idx < total; idx++) {
		if (label_res[idx] != 0) {
			u64_List_append(&eList[label_res[idx] - 1], idx);
		}
	}

	// 初始化返回结果
	uint64* result = (uint64*)calloc(label_num, sizeof(uint64));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in line %d of calc_gc.c \r\n", __LINE__);
		exit(-1);
	}

	// 定义中间变量
	register uint64 r_sum = 0, c_sum = 0;
	register uint64 r_idx = 0, c_idx = 0;
	register uint64 gc_ridx = 0, gc_cidx = 0;

	// 计算几何中心
	for (uint i = 0; i < label_num; i++) {

		r_sum = c_sum = 0;
		for (uint64 j = 0; j < eList[i].length; j++) {

			r_idx = eList[i].List[j] / cols64;
			c_idx = eList[i].List[j] % cols64;

			r_sum += r_idx;
			c_sum += c_idx;
		}
		gc_ridx = r_sum / eList[i].length;
		gc_cidx = c_sum / eList[i].length;

		result[i] = gc_ridx * cols64 + gc_cidx;
	}

	// 释放内存
	for (uint i = 0; i < label_num; i++) {
		free(eList[i].List);
		eList[i].List = NULL;
	}
	free(eList);
	eList = NULL;

	return result;
}
