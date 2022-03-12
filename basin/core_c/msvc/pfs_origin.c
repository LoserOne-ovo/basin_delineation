#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "type_aka.h"
#include "pfs_origin.h"
#include "paint_up.h"


int _pfs_r_uint8(int outlet_ridx, int outlet_cidx, unsigned char* basin, unsigned char* re_dir, float* upa, 
				 int* sub_outlets, float ths, int rows, int cols) {

	// ��ʼ��
	uint64 cols64 = (uint64)cols;
	uint64 total_num = rows * cols64;
	uint64 idx = outlet_ridx * cols64 + outlet_cidx;
	uint64 upper_idx = 0;;
	uint8 reverse_dir = 0;
	float temp_upa = 0.0;

	Tribu main_tribus[4];
	memset(main_tribus, 0, sizeof(main_tribus));
	float min_upa = 0.0;  // ��С֧���ļ�ˮ�����
	int min_upa_probe = 0;  // ��С֧���������е�λ��
	float upa_ths[2] = { 0.0,0.0 }; // �洢������֧���ļ�ˮ�����
	uint64 mt_idx[2] = { 0,0 }; // �洢��֧������ʱ��������֧����ˮ�ڵ�λ������

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };


	// �ӳ�ˮ��������׷��
	while (upa[idx] >= ths) {
		reverse_dir = re_dir[idx];
		if (reverse_dir == 0) {
			break; // ��������߽磬���˳�ѭ��
		}
		for (int p = 0; p < 8; p++) {
			// �ж��Ƿ�Ϊ����
			if (reverse_dir >= div[p]) {
				upper_idx = idx + offset[p];
				temp_upa = upa[upper_idx];
				
				// �жϻ����ۻ����Ƿ��㹻��Ϊһ��֧��
				// һ����Ԫֻ������һ��֧��ע�룬������������Ϊ�������δ������Ϊ֧�����������Ϊ�Ǳ��ػ�ˮ��
				if (temp_upa > ths) {
					// �������֪�ĸ����󣬾Ͱ�ԭʼ�ĸ�����Ϊ֧��������Ԫ��Ϊ����
					if (temp_upa > upa_ths[0]) {
						upa_ths[1] = upa_ths[0];
						upa_ths[0] = temp_upa;
						mt_idx[1] = mt_idx[0];
						mt_idx[0] = upper_idx;
					}
					// ����ȸ���С�� ��֧���󣬾��ø���Ԫ�滻֧��
					else if (temp_upa > upa_ths[1]) {
						upa_ths[1] = temp_upa;
						mt_idx[1] = upper_idx;
					}
					// �ȸ�����֧����ҪС���Ͳ�������
					else {
						;
					}
				}
				reverse_dir -= div[p];
			}
		}

		// �������֧��
		if (mt_idx[1] != 0) {
			// ���������֪����С֧��������в������
			if (upa_ths[1] > min_upa) {
				_tribu_insert(main_tribus, upa_ths[1], mt_idx[1], mt_idx[0], &min_upa, &min_upa_probe);
			}
		}
		idx = mt_idx[0];
		memset(upa_ths, 0, sizeof(upa_ths));
		memset(mt_idx, 0, sizeof(mt_idx));
	}

	// �ж��м���������
	uint8 tribu_num = 0;
	for (int i = 0; i < 4; i++) {
		if (main_tribus[i].upa != 0) {
			tribu_num++;
		}
	}
	int basin_num = 2 * tribu_num + 1;

	// ׼����ɫ��
	uint8* colors = (uint8*)calloc(basin_num, sizeof(unsigned char));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int i = 0; i < basin_num; i++) {
		colors[i] = i + 1;
	}
	// ׼��������ʼλ��
	uint64* basin_outlets = (uint64*)calloc(basin_num, sizeof(unsigned long long));
	if (basin_outlets == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	basin_outlets[0] = outlet_ridx * cols64 + outlet_cidx;
	uint8 probe = 1;
	for (uint8 i = 4 - tribu_num; i < 4; i++) {
		basin_outlets[probe] = main_tribus[i].tri_idx;
		probe++;
		basin_outlets[probe] = main_tribus[i].tru_idx;
		probe++;
	}

	// ������򱻷ֳ�9�ݣ��Ȼ������������ٻ�����������Ҫ���� (21 / 9) * basin_size��
	// ���Ҫ�����ظ����ƣ�����Ҫ�Ȼ������������ٻ����������򣬻�������baisn_size�αȽ����㣬���ܻ����
	// �ʲ��õ�һ�ַ���
	double compress = 1.0 / 10; // Ĭ��ջ��СΪ����Ӱ���1/10
	_paint_up_uint8(basin_outlets, colors, basin_num, compress, basin, re_dir, rows, cols);

	// �����������ˮ����Ϣ
	for (int i = 0; i < basin_num; i++) {
		sub_outlets[2 * i + 2] = (int)(basin_outlets[i] / cols64);
		sub_outlets[2 * i + 3] = (int)(basin_outlets[i] % cols64);
	}

	return basin_num;
}



int _tribu_insert(Tribu src[], float upa, unsigned long long tribu_idx, unsigned long long trunk_idx, float* min_upa, int* min_upa_probe) {

	// �ڲ���λ��֮���Ԫ��ȫ����ǰ��һλ
	for (int i = *min_upa_probe; i < 3; i++) {
		src[i].upa = src[i + 1].upa;
		src[i].tri_idx = src[i + 1].tri_idx;
		src[i].tru_idx = src[i + 1].tru_idx;
	}
	
	// �����һλ����
	src[3].upa = upa;
	src[3].tri_idx = tribu_idx;
	src[3].tru_idx = trunk_idx;
	
	// ����Ѱ����С��֧��
	*min_upa = src[0].upa;
	*min_upa_probe = 0;
	for (int j = 1; j < 4; j++) {
		if (src[j].upa < *min_upa) {
			*min_upa_probe = j;
			*min_upa = src[j].upa;
		}
	}
	
	return 1;
}

