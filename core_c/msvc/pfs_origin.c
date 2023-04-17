#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include "pfs_origin.h"
#include "paint_up.h"
#include "get_reverse_fdir.h"


int32_t _tribu_insert(Tribu src[], float upa, uint64_t* node, float* min_upa, int32_t* min_upa_probe) {

	// 在插入位置之后的元素全部向前移一位
	for (int32_t i = *min_upa_probe; i < 3; i++) {
		src[i].upa = src[i + 1].upa;
		src[i].tri_idx = src[i + 1].tri_idx;
		src[i].tru_idx = src[i + 1].tru_idx;
		src[i].nex_idx = src[i + 1].nex_idx;
	}
	
	// 在最后一位插入
	src[3].upa = upa;
	src[3].nex_idx = node[2];
	src[3].tri_idx = node[1];
	src[3].tru_idx = node[0];
	
	// 重新寻找最小的支流
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
	float min_upa = 0.0;  // 最小支流的集水区面积
	int32_t min_upa_probe = 0;  // 最小支流在数组中的位置
	float upa_ths[2] = { 0.0,0.0 }; // 存储干流和支流的集水区面积
	uint64_t mt_idx[3] = { 0,0,0 }; // 存储干支流划分时，干流和支流出水口的位置索引
	
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// 从出水口往上游追踪
	while (upa[idx] > ths) {
		
		reverse_dir = re_dir[idx];
		if (reverse_dir == 0) {
			break; // 到达流域边界，则退出循环
		}
		mt_idx[2] = idx;
		// 如果是上游流域的入水口
		// 不能产生干流，只能产生支流
		if (idx == inlet_idx) {
			// 判断是否为上游
			for (p = 0; p < 8; p++) {
				if (reverse_dir & div[p]) {
					upper_idx = idx + offset[p];
					temp_upa = upa[upper_idx];
					// 如果比已知的支流大， 比支流大，就用该像元替换支流
					if (temp_upa > ths && temp_upa > upa_ths[1]) {
						upa_ths[1] = temp_upa;
						mt_idx[1] = upper_idx;
					}
				}
			}
			// 如果大于已知的最小支流，则进行插入操作
			if (upa_ths[1] > min_upa) {
				_tribu_insert(main_tribus, upa_ths[1], mt_idx, &min_upa, &min_upa_probe);
			}
			break;
		}
		for (p = 0; p < 8; p++) {
			// 判断是否为上游
			if (reverse_dir & div[p]) {
				upper_idx = idx + offset[p];
				temp_upa = upa[upper_idx];

				// 判断汇流累积量是否足够作为一条支流
				// 一个像元只允许有一个支流注入，所以最大的上游为干流，次大的上游为支流，其余的认为是本地汇水区
				if (temp_upa > ths) {
					// 如果比已知的干流大，就把原始的干流设为支流，该像元设为干流
					if (temp_upa > upa_ths[0]) {
						upa_ths[1] = upa_ths[0];
						upa_ths[0] = temp_upa;
						mt_idx[1] = mt_idx[0];
						mt_idx[0] = upper_idx;
					}
					// 如果比干流小， 比支流大，就用该像元替换支流
					else if (temp_upa > upa_ths[1]) {
						upa_ths[1] = temp_upa;
						mt_idx[1] = upper_idx;
					}
					// 比干流和支流都要小，就不做处理
					else {
						;
					}
				}
			}
		}

		// 如果大于已知的最小支流，则进行插入操作
		if (upa_ths[1] > min_upa) {
			_tribu_insert(main_tribus, upa_ths[1], mt_idx, &min_upa, &min_upa_probe);
		}

		idx = mt_idx[0];
		memset(upa_ths, 0, sizeof(upa_ths));
		memset(mt_idx, 0, sizeof(mt_idx));
	}

	// 判断有几个子流域
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
		// 干流. 注意type=2时，最后一个承接上游来水的流域可能缺失。
		idx = main_tribus[p - 1].tru_idx;
		if (idx != 0) {
			_paint_upper_unpainted_uint8(idx, color, stack, basin, re_dir, offset, div);
			sub_outlets[2 * color] = (int32_t)(idx / cols64);
			sub_outlets[2 * color + 1] = (int32_t)(idx % cols64);
			sub_inlets[2 * color] = (int32_t)(temp_inlet_idx / cols64);
			sub_inlets[2 * color + 1] = (int32_t)(temp_inlet_idx % cols64);
			--color;
		}
		// 支流
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

	// 将流域分为N份，平均面积为avg_area
	avg_area = area / decompose_num;

	// 从上游向下游寻找
	while (idx != outlet_idx) {
		upa_diff_2 = upa_diff_1;
		upa_diff_1 = upa[idx] - upstream_area;	
		// 如果当前流域的面积大于平均面积，则停止向下游寻找
		// 比较当前像元和上游下游与期望面积的差值，取较小的那个
		if (upa_diff_1 >= avg_area) {
			// 如果下游像元的流域面积更接近期望面积
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
			// 如果上游像元的流域面积更接近期望面积
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
			// 如果剩下最后一个流域
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
