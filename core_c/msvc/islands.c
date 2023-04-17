#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "paint_up.h"


//int32_t* _argqsort_float(float* __restrict src, int32_t length);
//void _argsort_float_step(float* __restrict sorted, int32_t* __restrict argsorted, int32_t low, int32_t high);


int32_t _calc_island_statistics_int32(int32_t* __restrict island_label, int32_t island_num, double* __restrict area, int32_t* __restrict envelope, 
	uint8_t* __restrict dir, float* __restrict upa, int32_t rows, int32_t cols) {

	/*
		area:     shape = (island_num * 1), dtype=float，岛屿外流区的面积
		envelope: shape = (island_num * 4), dtype=int32_t，  岛屿的外包矩形
	*/

	uint64_t idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	int32_t island_id = 0;
	int32_t tuple_id = 0;
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const uint8_t dir_up[8] = { 8, 4, 2, 1, 128, 64, 32, 16 };


	for (int32_t i = 0; i < rows; i++) {
		for (int32_t j = 0; j < cols; j++) {
			island_id = island_label[idx];
			if (island_id > 0) {
				// 计算外包矩形
				tuple_id = island_id * 4;
				envelope[tuple_id] = i < envelope[tuple_id] ? i : envelope[tuple_id]; // 最小行号
				envelope[tuple_id + 1] = j < envelope[tuple_id + 1] ? j : envelope[tuple_id + 1]; // 最小列号
				envelope[tuple_id + 2] = i > envelope[tuple_id + 2] ? i : envelope[tuple_id + 2]; // 最大行号
				envelope[tuple_id + 3] = j > envelope[tuple_id + 3] ? j : envelope[tuple_id + 3]; // 最大列号
				// 计算外流面积
				area[island_id] += upa[idx];
			}
			idx++;
		}
	}
	return 1;
}


int32_t _island_paint_uint8(uint64_t* __restrict idxs, uint8_t* __restrict colors, int32_t island_num, uint8_t* __restrict dir, 
	uint8_t* __restrict re_dir, uint8_t* __restrict basin, int32_t rows, int32_t cols)
{
	int32_t i = 0, j = 0;
	uint8_t color;
	double frac = 0.03;
	uint64_t idx, temp_idx;
	uint64_t cols64 = (uint64_t)cols;
	uint64_t STACK_SIZE = ((uint64_t)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}

	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);
	u64_DynArray* coast = u64_DynArray_Initial((rows + cols64) * 2);

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const int32_t offset_4[4] = { 1, -1, cols, -cols };


	for (i = 0; i < island_num; i++) {

		idx = idxs[i];
		color = colors[i];
		basin[idx] = color;

		coast->length = 0;
		stack->length = 0;
		stack->data[stack->length++] = idx;
		coast->data[coast->length++] = idx;

		while (stack->length > 0) {
			idx = stack->data[--stack->length];
			for (j = 0; j < 4; j++) {
				temp_idx = idx + offset_4[j];
				if (dir[temp_idx] == 0 && basin[temp_idx] == 0) {
					basin[temp_idx] = color;
					u64_DynArray_Push(coast, temp_idx);
					u64_DynArray_Push(stack, temp_idx);
				}
			}
		}

		for (j = 0; j < coast->length; j++) {
			_paint_upper_uint8(coast->data[j], color, stack, basin, re_dir, offset, div);
		}
	}

	u64_DynArray_Destroy(stack);
	u64_DynArray_Destroy(coast);

	return 1;
}


int32_t _island_paint_int32(uint64_t* __restrict idxs, int32_t* __restrict colors, int32_t island_num, uint8_t* __restrict dir, 
	uint8_t* __restrict re_dir, int32_t* __restrict basin, int32_t rows, int32_t cols)
{
	int32_t i = 0, j = 0;
	int32_t color;
	double frac = 0.03;
	uint64_t idx, temp_idx;
	uint64_t cols64 = (uint64_t)cols;
	uint64_t STACK_SIZE = ((uint64_t)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}

	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);
	u64_DynArray* coast = u64_DynArray_Initial((rows + cols64) * 2);

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const int32_t offset_4[4] = { 1, -1, cols, -cols };


	for (i = 0; i < island_num; i++) {
		idx = idxs[i];
		color = colors[i];
		basin[idx] = color;

		coast->length = 0;
		stack->length = 0;
		stack->data[stack->length++] = idx;
		coast->data[coast->length++] = idx;

		while (stack->length > 0) {
			idx = stack->data[--stack->length];
			for (j = 0; j < 4; j++) {
				temp_idx = idx + offset_4[j];
				if (dir[temp_idx] == 0 && basin[temp_idx] == 0) {
					basin[temp_idx] = color;
					u64_DynArray_Push(coast, temp_idx);
					u64_DynArray_Push(stack, temp_idx);
				}
			}
		}

		for (j = 0; j < coast->length; j++) {
			_paint_upper_int32(coast->data[j], color, stack, basin, re_dir, offset, div);
		}
	}

	u64_DynArray_Destroy(stack);
	u64_DynArray_Destroy(coast);

	return 1;
}



int32_t _get_basin_area(uint8_t* __restrict basin, float* __restrict upa, double* __restrict basin_area, int32_t rows, int32_t cols) {

	uint64_t total_num = rows * (uint64_t)cols;
	uint64_t idx = 0;
	uint8_t basin_id = 0;

	for (idx = 0; idx < total_num; ++idx) {
		basin_id = basin[idx];
		if (basin_id != 0) {
			basin_area[basin_id] += upa[idx];
		}
	}
	return 1;
}



int32_t _get_coastal_line(uint64_t* __restrict idxs, uint8_t* __restrict colors, int32_t island_num, uint8_t* __restrict dir, 
	uint8_t* __restrict edge, int32_t rows, int32_t cols)
{
	int32_t i = 0, j = 0;
	uint8_t color;
	double frac = 0.03;
	uint64_t idx, temp_idx;
	uint64_t cols64 = (uint64_t)cols;

	u64_DynArray* coast = u64_DynArray_Initial((rows + cols64) * 2);

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const int32_t offset_4[4] = { 1, -1, cols, -cols };


	for (i = 0; i < island_num; i++) {

		idx = idxs[i];
		color = colors[i];
		edge[idx] = color;

		coast->length = 0;
		coast->data[coast->length++] = idx;

		while (coast->length > 0) {
			idx = coast->data[--coast->length];
			for (j = 0; j < 4; j++) {
				temp_idx = idx + offset_4[j];
				if (dir[temp_idx] == 0 && edge[temp_idx] == 0) {
					edge[temp_idx] = color;
					u64_DynArray_Push(coast, temp_idx);
				}
			}
		}
	}

	u64_DynArray_Destroy(coast);

	return 1;
}



//int32_t _island_merge(float* __restrict center_ridx, float* __restrict center_cidx, float* __restrict radius,
//	int32_t island_num, uint8_t* merge_flag) {
//
//	/*初始化参数*/
//	int32_t i, j;
//	int32_t coded = 0, uncoded = 0;
//	float shortest_dst;
//
//	// 未岛屿之间的距离矩阵分配内存
//	float** dst_matrix = (float**)malloc(island_num * sizeof(float*));
//	if (dst_matrix == NULL) {
//		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
//		exit(-1);
//	}
//	for (i = 0; i < island_num; i++) {
//		dst_matrix[i] = (float*)malloc(island_num * sizeof(float));
//		if (dst_matrix[i] == NULL) {
//			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
//			exit(-1);
//		}
//	}
//
//	// 计算岛屿之间的距离, doube -> float
//	double r_diff = 0.f;
//	double c_diff = 0.f;
//	for (i = 0; i < island_num; i++) {
//		for (j = 0; j < i; j++) {
//			r_diff = center_ridx[i] - center_ridx[j];
//			c_diff = center_cidx[i] - center_cidx[j];
//			dst_matrix[i][j] = sqrt(r_diff * r_diff + c_diff * c_diff) - radius[i] - radius[j];
//		}
//		dst_matrix[i][i] = 9999999.f;
//	}
//	for (int32_t i = 0; i < island_num; i++) {
//		for (j = i + 1; j < island_num; j++) {
//			dst_matrix[i][j] = dst_matrix[j][i];
//		}
//	}
//
//
//	// 排序岛屿之间的距离
//	int32_t** sort_martix = (int32_t**)malloc(island_num * sizeof(int32_t*));
//	if (sort_martix == NULL) {
//		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
//		exit(-1);
//	}
//	for (i = 0; i < island_num; i++) {
//		sort_martix[i] = _argqsort_float(dst_matrix[i], island_num - 1);
//	}
//
//
//	// 统计编码岛屿数量
//	int32_t merge_num = 0;
//	for (i = 0; i < island_num; i++) {
//		if (merge_flag[i] != 0) {
//			++merge_num;
//		}
//	}
//	// 辅助数组，标记每个编码岛屿最近的未编码岛屿
//	int32_t* auxi_arr = (int32_t*)calloc(island_num, sizeof(int32_t));
//	if (auxi_arr == NULL) {
//		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
//		exit(-1);
//	}
//
//	while (merge_num < island_num) {
//		shortest_dst = 99999999.f;
//		// 找到离现有编码岛屿最近的一个未编码岛屿
//		for (i = 0; i < island_num; i++) {
//			// 找一个编码岛屿
//			if (merge_flag[i] != 0) {
//				// 找最近的一个未编码岛屿
//				for (j = auxi_arr[i]; j < island_num; j++) {
//					if (merge_flag[j] == 0) {
//						// 与已知的最短距离相比较
//						if (dst_matrix[i][j] < shortest_dst) {
//							shortest_dst = dst_matrix[i][j];
//							coded = i;
//							uncoded = j;
//						}
//						else {
//							break;
//						}
//					}
//					else {
//						++auxi_arr[i];
//					}
//				}
//			}
//		}
//		merge_flag[uncoded] = merge_flag[coded];
//	}
//
//	/*释放内存*/
//	free(auxi_arr);
//	for (i = 0; i < island_num; i++) {
//		free(dst_matrix[i]);
//		free(sort_martix[i]);
//	}
//	free(dst_matrix);
//	free(sort_martix);
//
//	return 1;
//}
//
//int32_t* _argqsort_float(float* __restrict src, int32_t length) {
//
//
//	// 复制初始数组
//	float* sorted = (float*)malloc(length * sizeof(float));
//	if (sorted == NULL) {
//		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
//		exit(-1);
//	}
//	memcpy(sorted, src, length * sizeof(float));
//
//	// 初始化索引排序结果
//	int32_t* argsorted = (int32_t*)malloc(length * sizeof(int32_t));
//	if (argsorted == NULL) {
//		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
//		exit(-1);
//	}
//	for (int32_t i = 0; i < length; i++) {
//		argsorted[i] = i;
//	}
//
//	_argsort_float_step(sorted, argsorted, 0, length - 1);
//	free(sorted);
//
//	return argsorted;
//}
//
//void _argsort_float_step(float* __restrict sorted, int32_t* __restrict argsorted, int32_t low, int32_t high) {
//
//
//	if (high <= low) return;
//	int32_t i = low;
//	int32_t j = high + 1;
//	float key = sorted[low];
//	int32_t key_idx = argsorted[low];
//	float temp_val;
//	int32_t temp_idx;
//
//	while (1)
//	{
//		/*从左向右找比key大的值*/
//		while (sorted[++i] < key)
//		{
//			if (i == high) {
//				break;
//			}
//		}
//		/*从右向左找比key小的值*/
//		while (sorted[--j] > key)
//		{
//			if (j == low) {
//				break;
//			}
//		}
//		if (i >= j) break;
//		/*交换i,j对应的值*/
//		temp_val = sorted[i];
//		sorted[i] = sorted[j];
//		sorted[j] = temp_val;
//		temp_idx = argsorted[i];
//		argsorted[i] = argsorted[j];
//		argsorted[j] = temp_idx;
//	}
//	/*中枢值与j对应值交换*/
//	sorted[low] = sorted[j];
//	sorted[j] = key;
//	argsorted[low] = argsorted[j];
//	argsorted[j] = key_idx;
//
//	_argsort_float_step(sorted, argsorted, low, j - 1);
//	_argsort_float_step(sorted, argsorted, j + 1, high);
//
//}