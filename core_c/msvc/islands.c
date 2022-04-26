#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "type_aka.h"
#include "list.h"



int* _argqsort_float(float* __restrict src, int length);
void _argsort_float_step(float* __restrict sorted, int* __restrict argsorted, int low, int high);


int _calc_island_statistics_uint32(unsigned int* __restrict island_label, unsigned int island_num, float*__restrict center, int* __restrict sample,
	float* __restrict area, float* __restrict ref_area, int* __restrict envelope, unsigned char* __restrict dir, float* __restrict upa, int rows, int cols) {

	/*
		center:   shape = (island_num * 2), dtype=float，岛屿外包矩形中心的位置索引
		sample:   shape = (island_num * 2), dtype=int，  岛屿样点的位置索引
		area:     shape = (island_num * 1), dtype=float，岛屿外流区的面积
		ref_area: shape = (island_num * 1), dtype=float，岛屿单个像元的参考面积
		envelope: shape = (island_num * 4), dtype=int，  岛屿的外包矩形
	*/

	uint64 idx = 0;
	uint64 total_num = rows * (uint64)cols;
	uint island_id = 0, ref_island_id = 0;
	uint tuple_id = 0;
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const uint8 dir_up[8] = { 8, 4, 2, 1, 128, 64, 32, 16 };


	// 标记数组，标记岛屿样点是否已经采集
	uint8* __restrict sample_flag = (uint8*)calloc(island_num, sizeof(uint8));
	if (sample_flag == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	for (int i = 0; i < rows; i++) {
		for (int j = 0; j < cols; j++) {
			island_id = island_label[idx];
			if (island_id > 0) {

				ref_island_id = island_id - 1;
				
				// 取样点
				if (sample_flag[ref_island_id] == 0) {
					sample[2 * ref_island_id] = i;
					sample[2 * ref_island_id + 1] = j;
					sample_flag[ref_island_id] = 1;
				}

				// 计算外包矩形
				tuple_id = 4 * (island_id - 1);
				envelope[tuple_id] = i < envelope[tuple_id] ? i : envelope[tuple_id]; // 最小行号
				envelope[tuple_id + 1] = j < envelope[tuple_id + 1] ? j : envelope[tuple_id + 1]; // 最小列号
				envelope[tuple_id + 2] = i > envelope[tuple_id + 2] ? i : envelope[tuple_id + 2]; // 最大行号
				envelope[tuple_id + 3] = j > envelope[tuple_id + 3] ? j : envelope[tuple_id + 3]; // 最大列号

				// 计算外流面积
				area[ref_island_id] += upa[idx];
			}
			idx++;
		}
	}

	// 计算外包矩形中心和半径
	uint center_probe = 0;
	float ref_cell_area = 0.f;
	uint64 cols64 = (uint64)cols;
	uint64 center_idx = 0, temp_idx = 0;
	
	for (uint i = 0; i < island_num * 4; i += 4) {
		
		center[center_probe] = (envelope[i] + envelope[i + 2] + 1) / 2.0F;
		center[center_probe + 1] = (envelope[i + 1] + envelope[i + 3] + 1) / 2.0F;

		center_idx = (uint64)center[center_probe] * cols64 + (uint64)center[center_probe + 1];
		if (dir[center_idx] == 247) {
			center_idx = sample[center_probe] * cols64 + (uint64)sample[center_probe + 1];
		}
		ref_cell_area = upa[center_idx];
		

		for (int p = 0; p < 8; p++) {
			temp_idx = center_idx + offset[p];
			if (dir[temp_idx] == dir_up[p]) {
				ref_cell_area -= upa[temp_idx];
			}
		}
		ref_area[(int)(center_probe / 2)] = ref_cell_area;

		center_probe += 2;
	}

	// 释放内存
	free(sample_flag);
	sample_flag = NULL;

	return 1;
}


int _update_island_label_uint32(unsigned int* __restrict island_label, unsigned int island_num, unsigned int* __restrict new_label, int rows, int cols) {

	uint64 total_num = rows * (uint64)cols;
	uint64 idx = 0;
	uint src_label = 0;

	for (idx = 0; idx < total_num; idx++) {
		src_label = island_label[idx];
		if (src_label > 0) {
			island_label[idx] = new_label[src_label];
		}
	}
	return 1;
}


int _island_merge(float* __restrict center_ridx, float* __restrict center_cidx, float*__restrict radius, 
	int island_num, unsigned char* merge_flag) {

	/*初始化参数*/
	int i, j;
	int coded = 0, uncoded = 0;
	float shortest_dst;

	// 未岛屿之间的距离矩阵分配内存
	float** dst_matrix = (float**)malloc(island_num * sizeof(float*));
	if (dst_matrix == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (i = 0; i < island_num; i++) {
		dst_matrix[i] = (float*)malloc(island_num * sizeof(float));
		if (dst_matrix[i] == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}
	}

	// 计算岛屿之间的距离, doube -> float
	double r_diff = 0.f;
	double c_diff = 0.f;
	for (i = 0; i < island_num; i++) {
		for (j = 0; j < i; j++) {
			r_diff = center_ridx[i] - center_ridx[j];
			c_diff = center_cidx[i] - center_cidx[j];
			dst_matrix[i][j] = sqrt(r_diff * r_diff + c_diff * c_diff) - radius[i] - radius[j];
		}
		dst_matrix[i][i] = 9999999.f;
	}
	for (int i = 0; i < island_num; i++) {
		for (j = i + 1; j < island_num; j++) {
			dst_matrix[i][j] = dst_matrix[j][i];
		}
	}


	// 排序岛屿之间的距离
	int **sort_martix = (int**)malloc(island_num * sizeof(int*));
	if (sort_martix == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (i = 0; i < island_num; i++) {
		sort_martix[i] = _argqsort_float(dst_matrix[i], island_num - 1);
	}


	// 统计编码岛屿数量
	int merge_num = 0;
	for (i = 0; i < island_num; i++) {
		if (merge_flag[i] != 0) {
			++merge_num;
		}
	}
	// 辅助数组，标记每个编码岛屿最近的未编码岛屿
	int* auxi_arr = (int*)calloc(island_num, sizeof(int));
	if (auxi_arr == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	
	while (merge_num < island_num) {
		shortest_dst = 99999999.f;
		// 找到离现有编码岛屿最近的一个未编码岛屿
		for (i = 0; i < island_num; i++) {
			// 找一个编码岛屿
			if (merge_flag[i] != 0) {
				// 找最近的一个未编码岛屿
				for (j = auxi_arr[i]; j < island_num; j++) {
					if (merge_flag[j] == 0) {
						// 与已知的最短距离相比较
						if (dst_matrix[i][j] < shortest_dst) {
							shortest_dst = dst_matrix[i][j];
							coded = i;
							uncoded = j;
						}
						else {
							break;
						}
					}
					else {
						++auxi_arr[i];
					}
				}
			}
		}
		merge_flag[uncoded] = merge_flag[coded];
	}

	/*释放内存*/
	free(auxi_arr);
	for (i = 0; i < island_num; i++) {
		free(dst_matrix[i]);
		free(sort_martix[i]);
	}
	free(dst_matrix);
	free(sort_martix);

	return 1;
}



int* _argqsort_float(float* __restrict src, int length) {


	// 复制初始数组
	float* __restrict sorted = (float*)malloc(length * sizeof(float));
	if (sorted == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	memcpy(sorted, src, length * sizeof(float));

	// 初始化索引排序结果
	int* __restrict argsorted = (int*)malloc(length * sizeof(int));
	if (argsorted == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int i = 0; i < length; i++) {
		argsorted[i] = i;
	}

	_argsort_float_step(sorted, argsorted, 0, length - 1);
	free(sorted);

	return argsorted;
}


void _argsort_float_step(float* __restrict sorted, int* __restrict argsorted, int low, int high) {


	if (high <= low) return;
	int i = low;
	int j = high + 1;
	float key = sorted[low];
	int key_idx = argsorted[low];
	float temp_val;
	int temp_idx;

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
