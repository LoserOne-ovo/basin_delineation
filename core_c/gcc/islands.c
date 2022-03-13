#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "type_aka.h"
#include "list.h"



int _calc_island_statistics_uint32(unsigned int* island_label, unsigned int island_num, float* center, int* sample, float* radius,
	                               float* area, float* ref_area, int* envelope, unsigned char* dir, float* upa, int rows, int cols) {

	/*
		center:   shape = (island_num * 2), dtype=float����������������ĵ�λ������
		sample:   shape = (island_num * 2), dtype=int��  ���������λ������
		radius:   shape = (island_num * 1), dtype=float������������εİ뾶
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
	uint8* sample_flag = (uint8*)calloc(island_num, sizeof(uint8));
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
	uint center_probe = 0, radius_probe = 0;
	float ref_cell_area = 0.f;
	float PI = 3.1415926F;
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
		radius[radius_probe] = sqrtf(area[radius_probe] / (ref_cell_area * PI));
		ref_area[radius_probe] = ref_cell_area;

		center_probe += 2;
		radius_probe++;
	}

	// �ͷ��ڴ�
	free(sample_flag);
	sample_flag = NULL;

	return 1;
}


int _update_island_label_uint32(unsigned int* island_label, unsigned int island_num, unsigned int* new_label, int rows, int cols) {

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











