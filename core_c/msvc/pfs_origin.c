#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include "pfs_origin.h"
#include "paint_up.h"
#include "get_reverse_fdir.h"


int32_t _tribu_insert(Tribu src[], float upa, uint64_t* node, float* min_upa, int32_t* min_upa_probe) {

	// �ڲ���λ��֮���Ԫ��ȫ����ǰ��һλ
	for (int32_t i = *min_upa_probe; i < 3; i++) {
		src[i].upa = src[i + 1].upa;
		src[i].tri_idx = src[i + 1].tri_idx;
		src[i].tru_idx = src[i + 1].tru_idx;
		src[i].nex_idx = src[i + 1].nex_idx;
	}
	
	// �����һλ����
	src[3].upa = upa;
	src[3].nex_idx = node[2];
	src[3].tri_idx = node[1];
	src[3].tru_idx = node[0];
	
	// ����Ѱ����С��֧��
	*min_upa = src[0].upa;
	*min_upa_probe = 0;
	for (int32_t j = 1; j < 4; j++) {
		if (src[j].upa < *min_upa) {
			*min_upa_probe = j;
			*min_upa = src[j].upa;
		}
	}
	
	return 1;
}


int32_t _pfafstetter_uint8(uint64_t outlet_idx, uint64_t inlet_idx, uint8_t* __restrict re_dir, float* __restrict upa, 
	uint8_t* __restrict basin, float ths, int32_t rows, int32_t cols, int32_t* __restrict sub_outlets, int32_t* __restrict sub_inlets) {

	// Auxiliary variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t upper_idx = 0;;
	uint64_t idx = outlet_idx;
	uint8_t reverse_dir = 0;
	float temp_upa = 0.0;
	int32_t p = 0;

	Tribu main_tribus[4];
	memset(main_tribus, 0, sizeof(main_tribus));
	float min_upa = 0.0;  // ��С֧���ļ�ˮ�����
	int32_t min_upa_probe = 0;  // ��С֧���������е�λ��
	float upa_ths[2] = { 0.0,0.0 }; // �洢������֧���ļ�ˮ�����
	uint64_t mt_idx[3] = { 0,0,0 }; // �洢��֧������ʱ��������֧����ˮ�ڵ�λ������
	
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// �ӳ�ˮ��������׷��
	while (upa[idx] > ths) {
		
		reverse_dir = re_dir[idx];
		if (reverse_dir == 0) {
			break; // ��������߽磬���˳�ѭ��
		}
		mt_idx[2] = idx;
		// ����������������ˮ��
		// ���ܲ���������ֻ�ܲ���֧��
		if (idx == inlet_idx) {
			// �ж��Ƿ�Ϊ����
			for (p = 0; p < 8; p++) {
				if (reverse_dir & div[p]) {
					upper_idx = idx + offset[p];
					temp_upa = upa[upper_idx];
					// �������֪��֧���� ��֧���󣬾��ø���Ԫ�滻֧��
					if (temp_upa > ths && temp_upa > upa_ths[1]) {
						upa_ths[1] = temp_upa;
						mt_idx[1] = upper_idx;
					}
				}
			}
			// ���������֪����С֧��������в������
			if (upa_ths[1] > min_upa) {
				_tribu_insert(main_tribus, upa_ths[1], mt_idx, &min_upa, &min_upa_probe);
			}
			break;
		}
		for (p = 0; p < 8; p++) {
			// �ж��Ƿ�Ϊ����
			if (reverse_dir & div[p]) {
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
			}
		}

		// ���������֪����С֧��������в������
		if (upa_ths[1] > min_upa) {
			_tribu_insert(main_tribus, upa_ths[1], mt_idx, &min_upa, &min_upa_probe);
		}

		idx = mt_idx[0];
		memset(upa_ths, 0, sizeof(upa_ths));
		memset(mt_idx, 0, sizeof(mt_idx));
	}

	// �ж��м���������
	uint8_t sub_basin_num = 1;
	uint8_t tribu_num = 0;
	for (p = 0; p < 4; p++) {
		if (main_tribus[p].tri_idx != 0) {
			++sub_basin_num;
			++tribu_num;
		}
		if (main_tribus[p].tru_idx != 0) {
			++sub_basin_num;
		}
	}

	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	double frac = 0.1;
	uint64_t STACK_SIZE = ((uint64_t)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	
	// initialize stack
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	// deal with each branch, from upstream to downstream
	uint8_t color = sub_basin_num;
	uint64_t temp_inlet_idx = inlet_idx;
	for (p = 4; p > 4 - tribu_num; p--) {
		// ����. ע��type=2ʱ�����һ���н�������ˮ���������ȱʧ��
		idx = main_tribus[p - 1].tru_idx;
		if (idx != 0) {
			_paint_upper_unpainted_uint8(idx, color, stack, basin, re_dir, offset, div);
			sub_outlets[2 * color] = (int32_t)(idx / cols64);
			sub_outlets[2 * color + 1] = (int32_t)(idx % cols64);
			sub_inlets[2 * color] = (int32_t)(temp_inlet_idx / cols64);
			sub_inlets[2 * color + 1] = (int32_t)(temp_inlet_idx % cols64);
			--color;
		}
		// ֧��
		idx = main_tribus[p - 1].tri_idx;
		_paint_upper_uint8(idx, color, stack, basin, re_dir, offset, div);
		sub_outlets[2 * color] = (int32_t)(idx / cols64);
		sub_outlets[2 * color + 1] = (int32_t)(idx % cols64);
		--color;
		temp_inlet_idx = main_tribus[p - 1].nex_idx;
	}

	// deal with the final outlet branch
	_paint_upper_unpainted_uint8(outlet_idx, color, stack, basin, re_dir, offset, div);
	sub_outlets[2 * color] = (int32_t)(outlet_idx / cols64);
	sub_outlets[2 * color + 1] = (int32_t)(outlet_idx % cols64);
	sub_inlets[2 * color] = (int32_t)(temp_inlet_idx / cols64);
	sub_inlets[2 * color + 1] = (int32_t)(temp_inlet_idx % cols64);

	// free memory
	u64_DynArray_Destroy(stack);

	// return the number of all sub basins
	return sub_basin_num;
}


int32_t _decompose_uint8(uint64_t outlet_idx, uint64_t inlet_idx, float area, int32_t decompose_num, 
	uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa, uint8_t* __restrict basin, 
	int32_t rows, int32_t cols, int32_t* __restrict sub_outlets, int32_t* __restrict sub_inlets)
{

	// Auxiliary variables
	uint64_t cols64 = (uint64_t)cols;
	uint64_t upper_idx = inlet_idx;;
	uint64_t idx = inlet_idx;
	uint64_t sub_inlet_idx = inlet_idx;
	uint64_t down_idx = 0;
	float upa_diff_1 = 0.f;
	float upa_diff_2 = 0.f;
	float avg_area = 0.f;
	float upstream_area = upa[outlet_idx] - area;
	uint8_t sub_basin_number = decompose_num;

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	
	// Calculate the depth of the stack with given fraction, up to 100,000,000.
	double frac = 0.1;
	uint64_t STACK_SIZE = ((uint64_t)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	// initialize stack
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	// �������ΪN�ݣ�ƽ�����Ϊavg_area
	avg_area = area / decompose_num;

	// ������������Ѱ��
	while (idx != outlet_idx) {
		upa_diff_2 = upa_diff_1;
		upa_diff_1 = upa[idx] - upstream_area;	
		// �����ǰ������������ƽ���������ֹͣ������Ѱ��
		// �Ƚϵ�ǰ��Ԫ��������������������Ĳ�ֵ��ȡ��С���Ǹ�
		if (upa_diff_1 >= avg_area) {
			// ���������Ԫ������������ӽ��������
			if (fabs(upa_diff_1) <= fabs(upa_diff_2)) {
				sub_outlets[2 * sub_basin_number] = (int32_t)(idx / cols64);
				sub_outlets[2 * sub_basin_number + 1] = (int32_t)(idx % cols64);
				sub_inlets[2 * sub_basin_number] = (int32_t)(sub_inlet_idx / cols64);
				sub_inlets[2 * sub_basin_number + 1] = (int32_t)(sub_inlet_idx % cols64);
				sub_inlet_idx = _get_down_idx64(dir[idx], idx, cols);
				upstream_area = upa[idx];
				_paint_upper_unpainted_uint8(idx, sub_basin_number, stack, basin, re_dir, offset, div);
				sub_basin_number--;
				upa_diff_1 = 0.0;
				avg_area = (upa[outlet_idx] - upstream_area) / sub_basin_number;
			}
			// ���������Ԫ������������ӽ��������
			else {
				sub_outlets[2 * sub_basin_number] = (int32_t)(upper_idx / cols64);
				sub_outlets[2 * sub_basin_number + 1] = (int32_t)(upper_idx % cols64);
				sub_inlets[2 * sub_basin_number] = (int32_t)(sub_inlet_idx / cols64);
				sub_inlets[2 * sub_basin_number + 1] = (int32_t)(sub_inlet_idx % cols64);
				sub_inlet_idx = idx;
				upstream_area = upa[upper_idx];
				_paint_upper_unpainted_uint8(upper_idx, sub_basin_number, stack, basin, re_dir, offset, div);
				sub_basin_number--;
				upa_diff_1 = 0.0;
				avg_area = (upa[outlet_idx] - upstream_area) / sub_basin_number;
			}
			// ���ʣ�����һ������
			if (sub_basin_number == 1) {
				sub_outlets[2 * sub_basin_number] = (int32_t)(outlet_idx / cols64);
				sub_outlets[2 * sub_basin_number + 1] = (int32_t)(outlet_idx % cols64);
				sub_inlets[2 * sub_basin_number] = (int32_t)(sub_inlet_idx / cols64);
				sub_inlets[2 * sub_basin_number + 1] = (int32_t)(sub_inlet_idx % cols64);
				_paint_upper_unpainted_uint8(outlet_idx, sub_basin_number, stack, basin, re_dir, offset, div);
				break;
			}
		}
		upper_idx = idx;
		idx = _get_down_idx64(dir[idx], idx, cols);
	}

	u64_DynArray_Destroy(stack);
	return 1;
}
