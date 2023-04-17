#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "sort.h"


void _argsort_float_step(float* __restrict sorted, int32_t* __restrict argsorted, int32_t low, int32_t high);


int32_t* _argqsort_float(float* __restrict src, int32_t length) {


	// 复制初始数组
	float* sorted = (float*)malloc(length * sizeof(float));
	if (sorted == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	memcpy(sorted, src, length * sizeof(float));

	// 初始化索引排序结果
	int32_t* argsorted = (int32_t*)malloc(length * sizeof(int32_t));
	if (argsorted == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int32_t i = 0; i < length; i++) {
		argsorted[i] = i;
	}

	_argsort_float_step(sorted, argsorted, 0, length - 1);
	free(sorted);

	return argsorted;
}

void _argsort_float_step(float* __restrict sorted, int32_t* __restrict argsorted, int32_t low, int32_t high) {


	if (high <= low) return;
	int32_t i = low;
	int32_t j = high + 1;
	float key = sorted[low];
	int32_t key_idx = argsorted[low];
	float temp_val;
	int32_t temp_idx;

	while (1)
	{
		/*从左向右找比key大的值*/
		while (sorted[++i] < key)
		{
			if (i == high) {
				break;
			}
		}
		/*从右向左找比key小的值*/
		while (sorted[--j] > key)
		{
			if (j == low) {
				break;
			}
		}
		if (i >= j) break;
		/*交换i,j对应的值*/
		temp_val = sorted[i];
		sorted[i] = sorted[j];
		sorted[j] = temp_val;
		temp_idx = argsorted[i];
		argsorted[i] = argsorted[j];
		argsorted[j] = temp_idx;
	}
	/*中枢值与j对应值交换*/
	sorted[low] = sorted[j];
	sorted[j] = key;
	argsorted[low] = argsorted[j];
	argsorted[j] = key_idx;

	_argsort_float_step(sorted, argsorted, low, j - 1);
	_argsort_float_step(sorted, argsorted, j + 1, high);

}