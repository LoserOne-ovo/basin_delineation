#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "calc_gc.h"


__declspec(dllexport) unsigned long long* calc_gc(unsigned int* label_res, unsigned int label_num, int rows, int cols)
{
	
	uint64 total = rows * (uint64)cols;
	uint64 idx = 0;

	edge_list* eList = (edge_list*)calloc(label_num, sizeof(edge_list));
	if (eList == NULL) {
		fprintf(stderr, "memory allocation failed in line %d of calc_gc.c \r\n", __LINE__);
		exit(-1);
	}
	
	// 初始化列表 
	for (uint i = 0; i < label_num; i++) {

		eList[i].length = 0;
		eList[i].List = (uint64*)calloc(EL_SIZE, sizeof(uint64));
		if (eList[i].List == NULL) {
			fprintf(stderr, "memory allocation failed in line %d of calc_gc.c \r\n", __LINE__);
			exit(-1);
		}
		eList[i].alloc_length = EL_SIZE;
		
	}


	for (idx = 0; idx < total; idx++) {
		if (label_res[idx] != 0) {
			eL_append(&eList[label_res[idx] - 1], idx);
		}
	}


	uint64* result = (uint64*)calloc(label_num, sizeof(uint64));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in line %d of calc_gc.c \r\n", __LINE__);
		exit(-1);
	}

	uint64 r_sum = 0, c_sum = 0;
	uint64 r_idx = 0, c_idx = 0;
	uint64 gc_ridx = 0, gc_cidx = 0;

	for (uint i = 0; i < label_num; i++) {

		r_sum = c_sum = 0;
		for (uint j = 0; j < eList[i].length; j++) {

			r_idx = eList[i].List[j] / cols;
			c_idx = eList[i].List[j] % cols;

			r_sum += r_idx;
			c_sum += c_idx;
		}
		gc_ridx = r_sum / eList[i].length;
		gc_cidx = c_sum / eList[i].length;

		result[i] = gc_ridx * cols + gc_cidx;
	}

	for (uint i = 0; i < label_num; i++) {
		free(eList[i].List);
		eList[i].List = NULL;
	}
	free(eList);
	eList = NULL;

	return result;
}


__declspec(dllexport) int islands_merge(unsigned int* label_res, unsigned short* basin, unsigned int label_num,
										int rows, int cols, unsigned short* colors) 
{

	uint64 total = rows * (uint64)cols;
	uint64 idx = 0;

	for (idx = 0; idx < total; idx++) {
		if (label_res[idx] != 0) {
			basin[idx] = colors[label_res[idx] - 1];
		}
	}
	
	return 1;
}


int eL_append(edge_list* src, unsigned long long elem) {

	// 检查是否需要重新分配内存
	if (src->length == src->alloc_length) {
		unsigned int new_size = src->alloc_length + EL_SIZE;
		uint64* temp = (uint64*)realloc(src->List, new_size * sizeof(uint64));
		if (temp == NULL) {
			fprintf(stderr, "memory reallocation failed in line %d of calc_gc.c \r\n", __LINE__);
			exit(-2);
		}
		src->List = temp;
		src->alloc_length = new_size;
	}

	src->List[src->length] = elem;
	src->length++;

	return 1;
}


