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
		center:   shape = (island_num * 2), dtype=float����������������ĵ�λ������
		sample:   shape = (island_num * 2), dtype=int��  ���������λ������
		area:     shape = (island_num * 1), dtype=float�����������������
		ref_area: shape = (island_num * 1), dtype=float�����쵥����Ԫ�Ĳο����
		envelope: shape = (island_num * 4), dtype=int��  ������������
	*/

	uint64 idx = 0;
	uint64 total_num = rows * (uint64)cols;
	uint island_id = 0, ref_island_id = 0;
	uint tuple_id = 0;
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const uint8 dir_up[8] = { 8, 4, 2, 1, 128, 64, 32, 16 };


	// ������飬��ǵ��������Ƿ��Ѿ��ɼ�
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
				
				// ȡ����
				if (sample_flag[ref_island_id] == 0) {
					sample[2 * ref_island_id] = i;
					sample[2 * ref_island_id + 1] = j;
					sample_flag[ref_island_id] = 1;
				}

				// �����������
				tuple_id = 4 * (island_id - 1);
				envelope[tuple_id] = i < envelope[tuple_id] ? i : envelope[tuple_id]; // ��С�к�
				envelope[tuple_id + 1] = j < envelope[tuple_id + 1] ? j : envelope[tuple_id + 1]; // ��С�к�
				envelope[tuple_id + 2] = i > envelope[tuple_id + 2] ? i : envelope[tuple_id + 2]; // ����к�
				envelope[tuple_id + 3] = j > envelope[tuple_id + 3] ? j : envelope[tuple_id + 3]; // ����к�

				// �����������
				area[ref_island_id] += upa[idx];
			}
			idx++;
		}
	}

	// ��������������ĺͰ뾶
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

	// �ͷ��ڴ�
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

	/*��ʼ������*/
	int i, j;
	int coded = 0, uncoded = 0;
	float shortest_dst;

	// δ����֮��ľ����������ڴ�
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

	// ���㵺��֮��ľ���, doube -> float
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


	// ������֮��ľ���
	int **sort_martix = (int**)malloc(island_num * sizeof(int*));
	if (sort_martix == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (i = 0; i < island_num; i++) {
		sort_martix[i] = _argqsort_float(dst_matrix[i], island_num - 1);
	}


	// ͳ�Ʊ��뵺������
	int merge_num = 0;
	for (i = 0; i < island_num; i++) {
		if (merge_flag[i] != 0) {
			++merge_num;
		}
	}
	// �������飬���ÿ�����뵺�������δ���뵺��
	int* auxi_arr = (int*)calloc(island_num, sizeof(int));
	if (auxi_arr == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	
	while (merge_num < island_num) {
		shortest_dst = 99999999.f;
		// �ҵ������б��뵺�������һ��δ���뵺��
		for (i = 0; i < island_num; i++) {
			// ��һ�����뵺��
			if (merge_flag[i] != 0) {
				// �������һ��δ���뵺��
				for (j = auxi_arr[i]; j < island_num; j++) {
					if (merge_flag[j] == 0) {
						// ����֪����̾�����Ƚ�
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

	/*�ͷ��ڴ�*/
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


	// ���Ƴ�ʼ����
	float* __restrict sorted = (float*)malloc(length * sizeof(float));
	if (sorted == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	memcpy(sorted, src, length * sizeof(float));

	// ��ʼ������������
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
		/*���������ұ�key���ֵ*/
		while (sorted[++i] < key)
		{
			if (i == high) {
				break;
			}
		}
		/*���������ұ�keyС��ֵ*/
		while (sorted[--j] > key)
		{
			if (j == low) {
				break;
			}
		}
		if (i >= j) break;
		/*����i,j��Ӧ��ֵ*/
		temp_val = sorted[i];
		sorted[i] = sorted[j];
		sorted[j] = temp_val;
		temp_idx = argsorted[i];
		argsorted[i] = argsorted[j];
		argsorted[j] = temp_idx;
	}
	/*����ֵ��j��Ӧֵ����*/
	sorted[low] = sorted[j];
	sorted[j] = key;
	argsorted[low] = argsorted[j];
	argsorted[j] = key_idx;

	_argsort_float_step(sorted, argsorted, low, j - 1);
	_argsort_float_step(sorted, argsorted, j + 1, high);

}
