#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "sinks.h"
#include "paint_up.h"
#include "envelope.h"
#include "sort.h"
#include "get_reverse_fdir.h"



int32_t _dissolve_sinks_uint16(uint16_t* __restrict basin, uint8_t* __restrict re_dir, float* __restrict dem, 
	uint64_t* __restrict sink_idxs, uint16_t sink_num, int32_t rows, int32_t cols, double frac) {


	uint64_t idx = 0;
	uint64_t cols64 = (uint64_t)cols;
	// 根据提供的比例，计算需要用到的栈深度（不要在意用stack命名栈）
	uint64_t STACK_SIZE = ((uint64_t)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	uint64_t RC_SIZE = 10000;
	uint16_t min_sink = 11;
	uint16_t* colors = u16_VLArray_Initial(sink_num, 0);
	for (uint16_t i = 0; i < sink_num; i++) {
		colors[i] = min_sink + i;
	}

	// 存储每一个内流区的边界像元
	u64_DynArray** rim_cell = (u64_DynArray**)calloc(sink_num, sizeof(u64_DynArray*));
	if (rim_cell == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint16_t i = 0; i < sink_num; i++) {
		rim_cell[i] = u64_DynArray_Initial(RC_SIZE);
	}

	// 初始化上游追踪需要的辅助数据
	uint8_t reverse_fdir = 0;
	uint16_t color = 0;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	
	// 循环绘制每一个内流区
	for (uint16_t i = 0; i < sink_num; i++) {

		// 读取内流区的绘图颜色信息
		color = colors[i];
		// 在不重新分配内存的情况下，清空栈，并压入内流区终点的位置索引
		stack->data[0] = sink_idxs[i];
		stack->length = 1;

		while (stack->length > 0) {
			idx = stack->data[stack->length - 1];
			basin[idx] = color;
			stack->length--;
			reverse_fdir = re_dir[idx];

			// 在追溯的过程中，如果一个像元没有上游，那么就认为是边界像元
			if (reverse_fdir == 0) {
				u64_DynArray_Push(rim_cell[i], idx);
			}
			// 如果有上游，则进行绘制
			else {
				for (int32_t p = 0; p < 8; p++) {
					if (reverse_fdir >= div[p]) {
						u64_DynArray_Push(stack, idx + offset[p]);
						reverse_fdir -= div[p];
					}
				}
			}
		}
	}

	// 将内流域合并到外流区，以外流区编号记录下合并结果
	uint16_t* merge_flag = _inner_merge_u16(basin, dem, rim_cell, sink_num, min_sink, offset);

	for (uint16_t i = 0; i < sink_num;i++) {
		u64_DynArray_Destroy(rim_cell[i]);
	}
	free(rim_cell);
	rim_cell = NULL;


	// 以新的编号重新追溯上游
	for (uint16_t i = 0;i < sink_num; i++) {

		idx = sink_idxs[i];
		color = merge_flag[i];
		stack->data[0] = idx;
		stack->length = 1;

		while (stack->length > 0) {
			idx = stack->data[stack->length - 1];
			basin[idx] = color;
			stack->length--;
			reverse_fdir = re_dir[idx];

			for (int32_t p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_DynArray_Push(stack, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
		}
	}

	u64_DynArray_Destroy(stack);
	free(merge_flag);
	free(colors);

	return 1;
}


uint16_t* _inner_merge_u16(uint16_t* __restrict basin, float* __restrict elev, u64_DynArray** rim_cell, uint16_t sink_num, uint16_t min_sink, const int32_t offset[])
{
	// 函数的返回结果，用于存储内流区被合并到哪个流域
	uint16_t* merge_flag = (uint16_t*)calloc(sink_num, sizeof(uint16_t));
	if (merge_flag == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	
	// 初始化辅助参数
	uint64_t CB_SIZE = 100;
	uint16_t wrong_tag = 10000;
	uint16_t next_basin = 0;
	u64_DynArray* temp;

	// 记录当前要处理的流域编号（一个内流区可能合并到另一个内流区），用于去除非边界像元
	u16_DynArray* cur_basin = (u16_DynArray*)malloc(sizeof(u16_DynArray));
	if (cur_basin == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	cur_basin->batch_size = CB_SIZE;
	cur_basin->data = (uint16_t*)calloc(CB_SIZE, sizeof(uint16_t));
	if (cur_basin->data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	cur_basin->alloc_length = CB_SIZE;
	cur_basin->data[0] = 0; // 第一位存储0，保证流域不被合并到数据范围之外
	cur_basin->length = 1;


	for (uint16_t i = 0; i < sink_num; i++) {

		// 尚未被合并
		if (merge_flag[i] == 0) {
			// 加入到当前待处理流域列表中
			u16_DynArray_Push(cur_basin, min_sink + i);
			// 去除流域内部的局部最高点
			temp = _remove_inner_peak_u16(rim_cell[i], basin, cur_basin, offset);
			
			// 错误情况：没有流域边界像元
			if (temp->length == 0) {
				// 给予该流域一个错误编号
				merge_flag[i] = wrong_tag++;
				// 重设辅助数据，并处理下一个流域
				cur_basin->length = 1;
				free(temp->data);
				free(temp);
				continue;
			}
			// 寻找合并到的下一个流域
			next_basin = _find_next_basin_u16(temp, elev, basin, cur_basin, offset);
			
			// 如果流域没有合并的外流区
			while (next_basin >= min_sink) {
				
				// 如果合并到一个没有处理过的内流区，继续合并
				if (merge_flag[next_basin - min_sink] == 0) {
					u16_DynArray_Push(cur_basin, next_basin);
					// 重新寻找流域边界和要合并到的流域
					temp = _eL_merge_u16(temp, rim_cell[next_basin - min_sink], basin, cur_basin, offset);
					next_basin = _find_next_basin_u16(temp, elev, basin, cur_basin, offset);
				}
				// 如果合并到已经处理过的内流区，停止合并
				else {
					break;
				}
			}

			// 没有边界像元的错误情况
			if (next_basin == 0) {
				for (uint32_t q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->data[q] - min_sink] = wrong_tag;
				}
				wrong_tag++;
			}
			// 正常情况
			else {
				
				// 合并到处理过的内流区，则合并到该内流区对应的外流区 
				if (next_basin >= min_sink) {
					next_basin = merge_flag[next_basin - min_sink];
				}
				// 合并
				for (uint32_t q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->data[q] - min_sink] = next_basin;
				}

			}
			cur_basin->length = 1;
			free(temp->data);
			free(temp);
		}
	}

	free(cur_basin->data);
	free(cur_basin);

	return merge_flag;
}


// 将流域内部的局部最高点和被海洋包围的边界点，从边界像元中除去
u64_DynArray* _remove_inner_peak_u16(u64_DynArray* src, uint16_t* basin, u16_DynArray* cur_color, const int32_t offset[]) {
	
	
	register uint64_t idx = 0;
	u64_DynArray* res = (u64_DynArray*)malloc(sizeof(u64_DynArray));
	if (res == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->data = (uint64_t*)calloc(src->length, sizeof(uint64_t));
	if (res->data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->batch_size = src->batch_size;
	res->alloc_length = src->length;

	for (uint64_t i = 0; i < src->length; i++) {
		for (int32_t j = 0; j < 8; j++) {
			idx = src->data[i] + offset[j];
			if (!check_in_u16_DynArray(basin[idx], cur_color)) {
				res->data[res->length++] = src->data[i];
				break;
			}
		}
	}

	return res;
}


//将两个流域的边界像元进行组合，需要重复remove_inner_peak操作
u64_DynArray* _eL_merge_u16(u64_DynArray* __restrict src, u64_DynArray* __restrict ins, uint16_t* basin, u16_DynArray* cur_basin, const int32_t offset[]){

	uint64_t idx = 0;
	uint64_t all_length = src->length + ins->length;
	
	u64_DynArray* res = (u64_DynArray*)malloc(sizeof(u64_DynArray));
	if (res == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->batch_size = src->batch_size;
	res->data = (uint64_t*)calloc(all_length, sizeof(uint64_t));
	if (res->data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->alloc_length = all_length;
	
	for (uint32_t i = 0; i < src->length; i++) {
		for (int32_t j = 0; j < 8; j++) {
			idx = src->data[i] + offset[j];
			if (!check_in_u16_DynArray(basin[idx], cur_basin)) {
				res->data[res->length++] = src->data[i];
				break;
			}
		}
	}
	
	for (uint32_t i = 0; i < ins->length; i++) {
		for (int32_t j = 0; j < 8; j++) {
			idx = ins->data[i] + offset[j];
			if (!check_in_u16_DynArray(basin[idx], cur_basin)) {
				res->data[res->length++] = ins->data[i];
				break;
			}
		}
	}
	
	free(src->data);
	free(src);
	src = NULL;

	return res;
}


uint16_t _find_next_basin_u16(u64_DynArray* edge_list, float* elev, uint16_t* basin, u16_DynArray* cur_basin, const int32_t offset[]) {

	// 初始化参数
	uint16_t next_basin = 0;
	float min_elev = 9999;
	float max_elev_diff = -9999, temp_elev_diff = 0;
	uint64_t min_idx = 0, temp_idx = 0;

	if (edge_list->length > 0) {
		// 先找到边界上的最低点
		for (uint32_t i = 0; i < edge_list->length;i++) {
			if (elev[edge_list->data[i]] < min_elev) {
				min_idx = edge_list->data[i];
				min_elev = elev[min_idx];
			}
		}
		// 再找高差最大的方向
		for (int32_t i = 0; i < 8; i++) {
			temp_idx = min_idx + offset[i];
			temp_elev_diff = elev[min_idx] - elev[temp_idx];
			if ((temp_elev_diff > max_elev_diff) &&
				!(check_in_u16_DynArray(basin[temp_idx], cur_basin))) {
				next_basin = basin[temp_idx];
				max_elev_diff = temp_elev_diff;
			}
		}
	}
	// 在没有边界像元的情况下返回0
	// 正常情况返回要合并入的流域的编号
	return next_basin;
}












int32_t _dissolve_sinks_uint8(uint8_t* __restrict basin, uint8_t* __restrict re_dir, float* __restrict dem, 
	uint64_t* __restrict sink_idxs, uint8_t sink_num, int32_t rows, int32_t cols, double frac) {

	uint64_t idx = 0;
	uint64_t cols64 = (uint64_t)cols;
	// 根据提供的比例，计算需要用到的栈深度
	uint64_t STACK_SIZE = ((uint64_t)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (STACK_SIZE > 100000000) {
		STACK_SIZE = 100000000;
	}
	// 假定的内流区边界像元数量
	uint64_t RC_SIZE = 10000;

	uint8_t min_sink = 11;
	uint8_t* colors = u8_VLArray_Initial(sink_num, 0);
	for (uint8_t i = 0; i < sink_num; i++) {
		colors[i] = min_sink + i;
	}

	// 存储每一个内流区的边界像元
	u64_DynArray** rim_cell = (u64_DynArray**)calloc(sink_num, sizeof(u64_DynArray*));
	if (rim_cell == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint8_t i = 0; i < sink_num; i++) {
		rim_cell[i] = u64_DynArray_Initial(RC_SIZE);
	}

	// 初始化上游追踪需要的辅助数据
	uint8_t reverse_fdir = 0;
	uint8_t color = 0;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);


	// 循环绘制每一个内流区
	for (uint8_t i = 0; i < sink_num; i++) {

		// 读取内流区的绘图颜色信息
		color = colors[i];
		// 在不重新分配内存的情况下，清空栈，并压入内流区终点的位置索引
		stack->data[0] = sink_idxs[i];
		stack->length = 1;

		while (stack->length > 0) {
			idx = stack->data[stack->length - 1];
			basin[idx] = color;
			stack->length--;
			reverse_fdir = re_dir[idx];

			// 在追溯的过程中，如果一个像元没有上游，那么就认为是边界像元
			if (reverse_fdir == 0) {
				u64_DynArray_Push(rim_cell[i], idx);
			}
			// 如果有上游，则进行绘制
			else {
				for (int32_t p = 0; p < 8; p++) {
					if (reverse_fdir >= div[p]) {
						u64_DynArray_Push(stack, idx + offset[p]);
						reverse_fdir -= div[p];
					}
				}
			}
		}
	}

	// 将内流域合并到外流区，以外流区编号记录下合并结果
	uint8_t* merge_flag = _inner_merge_u8(basin, dem, rim_cell, sink_num, min_sink, offset);

	for (uint8_t i = 0; i < sink_num;i++) {
		u64_DynArray_Destroy(rim_cell[i]);
	}
	free(rim_cell);
	rim_cell = NULL;


	// 以新的编号重新追溯上游
	for (uint8_t i = 0;i < sink_num; i++) {

		idx = sink_idxs[i];
		color = merge_flag[i];
		stack->data[0] = idx;
		stack->length = 1;

		while (stack->length > 0) {
			idx = stack->data[stack->length - 1];
			basin[idx] = color;
			stack->length--;
			reverse_fdir = re_dir[idx];

			for (int32_t p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_DynArray_Push(stack, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
		}
	}

	u64_DynArray_Destroy(stack);
	free(merge_flag);
	free(colors);

	return 1;
}


uint8_t* _inner_merge_u8(uint8_t* __restrict basin, float* __restrict elev, u64_DynArray** rim_cell, uint8_t sink_num, uint8_t min_sink, const int32_t offset[])
{
	// 函数的返回结果，用于存储内流区被合并到哪个流域
	uint8_t* merge_flag = (uint8_t*)calloc(sink_num, sizeof(uint8_t));
	if (merge_flag == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// 初始化辅助参数
	uint64_t CB_SIZE = 100;
	uint8_t wrong_tag = 100;
	uint8_t next_basin = 0;
	u64_DynArray* temp;

	// 记录当前要处理的流域编号（一个内流区可能合并到另一个内流区），用于去除非边界像元
	u8_DynArray* cur_basin = (u8_DynArray*)malloc(sizeof(u8_DynArray));
	if (cur_basin == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	cur_basin->batch_size = CB_SIZE;
	cur_basin->data = (uint8_t*)calloc(CB_SIZE, sizeof(uint8_t));
	if (cur_basin->data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	cur_basin->alloc_length = CB_SIZE;
	cur_basin->data[0] = 0; // 第一位存储0，保证流域不被合并到数据范围之外
	cur_basin->length = 1;


	for (uint8_t i = 0; i < sink_num; i++) {

		// 尚未被合并
		if (merge_flag[i] == 0) {
			// 加入到当前待处理流域列表中
			u8_DynArray_Push(cur_basin, min_sink + i);
			// 去除流域内部的局部最高点
			temp = _remove_inner_peak_u8(rim_cell[i], basin, cur_basin, offset);

			// 错误情况：没有流域边界像元
			if (temp->length == 0) {
				// 给予该流域一个错误编号
				merge_flag[i] = wrong_tag++;
				// 重设辅助数据，并处理下一个流域
				cur_basin->length = 1;
				free(temp->data);
				free(temp);
				continue;
			}
			// 寻找合并到的下一个流域
			next_basin = _find_next_basin_u8(temp, elev, basin, cur_basin, offset);

			// 如果流域没有合并的外流区
			while (next_basin >= min_sink) {

				// 如果合并到一个没有处理过的内流区，继续合并
				if (merge_flag[next_basin - min_sink] == 0) {
					u8_DynArray_Push(cur_basin, next_basin);
					// 重新寻找流域边界和要合并到的流域
					temp = _eL_merge_u8(temp, rim_cell[next_basin - min_sink], basin, cur_basin, offset);
					next_basin = _find_next_basin_u8(temp, elev, basin, cur_basin, offset);
				}
				// 如果合并到已经处理过的内流区，停止合并
				else {
					break;
				}
			}

			// 没有边界像元的错误情况
			if (next_basin == 0) {
				for (uint32_t q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->data[q] - min_sink] = wrong_tag;
				}
				wrong_tag++;
			}
			// 正常情况
			else {

				// 合并到处理过的内流区，则合并到该内流区对应的外流区 
				if (next_basin >= min_sink) {
					next_basin = merge_flag[next_basin - min_sink];
				}
				// 合并
				for (uint32_t q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->data[q] - min_sink] = next_basin;
				}

			}
			cur_basin->length = 1;
			free(temp->data);
			free(temp);
		}
	}

	free(cur_basin->data);
	free(cur_basin);

	return merge_flag;
}


/// <summary>
/// 将流域内部的局部最高点和被海洋包围的边界点，从边界像元中除去
/// </summary>
/// <param name="src"></param>
/// <param name="basin"></param>
/// <param name="cur_color"></param>
/// <param name="offset"></param>
/// <returns></returns>
u64_DynArray* _remove_inner_peak_u8(u64_DynArray* src, uint8_t* basin, u8_DynArray* cur_color, const int32_t offset[]) {


	register uint64_t idx = 0;
	u64_DynArray* res = (u64_DynArray*)malloc(sizeof(u64_DynArray));
	if (res == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->data = (uint64_t*)calloc(src->length, sizeof(uint64_t));
	if (res->data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->batch_size = src->batch_size;
	res->alloc_length = src->length;

	for (uint32_t i = 0; i < src->length; i++) {
		for (int32_t j = 0; j < 8; j++) {
			idx = src->data[i] + offset[j];
			if (!check_in_u8_DynArray(basin[idx], cur_color)) {
				res->data[res->length++] = src->data[i];
				break;
			}
		}
	}

	return res;
}


/// <summary>
/// 将两个流域的边界像元进行组合，需要重复remove_inner_peak操作
/// </summary>
/// <param name="src"></param>
/// <param name="ins"></param>
/// <param name="basin"></param>
/// <param name="cur_basin"></param>
/// <param name="offset"></param>
/// <returns></returns>
u64_DynArray* _eL_merge_u8(u64_DynArray* __restrict src, u64_DynArray* __restrict ins, uint8_t* basin, u8_DynArray* cur_basin, const int32_t offset[]) {

	register uint64_t idx = 0;
	uint64_t all_length = src->length + ins->length;

	u64_DynArray* res = (u64_DynArray*)malloc(sizeof(u64_DynArray));
	if (res == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->batch_size = src->batch_size;
	res->data = (uint64_t*)calloc(all_length, sizeof(uint64_t));
	if (res->data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->alloc_length = all_length;

	for (uint32_t i = 0; i < src->length; i++) {
		for (int32_t j = 0; j < 8; j++) {
			idx = src->data[i] + offset[j];
			if (!check_in_u8_DynArray(basin[idx], cur_basin)) {
				res->data[res->length++] = src->data[i];
				break;
			}
		}
	}

	for (uint32_t i = 0; i < ins->length; i++) {
		for (int32_t j = 0; j < 8; j++) {
			idx = ins->data[i] + offset[j];
			if (!check_in_u8_DynArray(basin[idx], cur_basin)) {
				res->data[res->length++] = ins->data[i];
				break;
			}
		}
	}

	free(src->data);
	free(src);
	src = NULL;

	return res;
}


uint8_t _find_next_basin_u8(u64_DynArray* edge_list, float* elev, uint8_t* basin, u8_DynArray* cur_basin, const int32_t offset[]) {

	// 初始化参数
	uint8_t next_basin = 0;
	float min_elev = 9999;
	float max_elev_diff = -9999, temp_elev_diff = 0;
	uint64_t min_idx = 0, temp_idx = 0;

	if (edge_list->length > 0) {
		// 先找到边界上的最低点
		for (uint32_t i = 0; i < edge_list->length;i++) {
			if (elev[edge_list->data[i]] < min_elev) {
				min_idx = edge_list->data[i];
				min_elev = elev[min_idx];
			}
		}
		// 再找高差最大的方向
		for (int32_t i = 0; i < 8; i++) {
			temp_idx = min_idx + offset[i];
			temp_elev_diff = elev[min_idx] - elev[temp_idx];
			if ((temp_elev_diff > max_elev_diff) &&
				!(check_in_u8_DynArray(basin[temp_idx], cur_basin))) {
				next_basin = basin[temp_idx];
				max_elev_diff = temp_elev_diff;
			}
		}
	}
	// 在没有边界像元的情况下返回0
	// 正常情况返回要合并入的流域的编号
	return next_basin;
}











int32_t _sink_union(int32_t* __restrict union_flag, int32_t* __restrict merge_flag, int32_t sink_num, int32_t* __restrict basin, int32_t rows, int32_t cols) {

	int32_t i, j, m, n, l;
	i = j = m = n = l = 0;
	uint64_t idx = 0;
	uint64_t cols64 = (uint64_t)cols;
	int32_t value = 0, src_value = 0;
	int32_t region_id = 0;
	int32_t result_flag = 1;

	// 开辟上三角矩阵，存储内流区的相邻信息
	uint8_t** utMatrix = u8_VLArray2D_Initial(sink_num + 1, sink_num + 1, 1);
	// 计算内流区的相邻关系和归属关系
	idx = cols64 + 1;
	for (i = 1; i < rows - 1; i++) {
		for (j = 1; j < cols - 1; j++) {
			src_value = basin[idx];
			// 如果是内流区像元，判断四邻域范围内是否有其他内流区或外流区
			if (src_value < 0) {
				// right pixel
				value = basin[idx + 1];
				if (value == 0 || value == src_value) {
					;
				}
				else if (value > 0) {
					merge_flag[-src_value] = value;
				}
				else {
					utMatrix[-src_value][-value] = 1;
				}
				// down pixel
				value = basin[idx + cols64];
				if (value == 0 || value == src_value) {
					;
				}
				else if (value > 0) {
					merge_flag[-src_value] = value;
				}
				else {
					utMatrix[-src_value][-value] = 1;
				}
			}
			++idx;
		}
		idx += 2;
	}

	// 计算内流区连通块数
	for (i = 1; i <= sink_num; i++) {
		for (j = i + 1; j <= sink_num; j++) {
			if (utMatrix[i][j] == 1 || utMatrix[j][i] == 1) {
				m = i;
				n = j;			
				while ((union_flag[n] != 0) && (union_flag[n] != m)) {
					l = union_flag[n];
					if (union_flag[n] < m) {
						n = m;
						m = l;
						
					}
					else {
						union_flag[n] = m;
						n = l;
					}
				}
				if (union_flag[n] == 0) {
					union_flag[n] = m;
				}
			}
		}
	}

	// 计算内流区的合并结果
	for (i = 1; i <= sink_num; i++) {
		if (union_flag[i] == 0) {
			union_flag[i] = ++region_id;
		}
		else {
			union_flag[i] = union_flag[union_flag[i]];
		}
	}

	// 检查内流区的归属，如果合并的内流区归属与不同的岛屿，则抛出错误
	int32_t* mArray = i32_VLArray_Initial(region_id + 1, 1);
	for (i = 1; i <= sink_num; i++) {
		if (merge_flag[i] > 0) {
			if (mArray[union_flag[i]] == 0) {
				mArray[union_flag[i]] = merge_flag[i];
			}
			else if (mArray[union_flag[i]] == merge_flag[i]) {
				continue;
			}
			else {
				fprintf(stderr, "can't locate adjacent sinks into the same island!\r\n");
				result_flag = -1;
			}
		}
	}

	// 检查是否所有的内流区是否都定位到了岛屿上
	for (i = 1; i <= region_id; i++) {
		if (mArray[i] == 0) {
			fprintf(stderr, "Can't locate adjacent sinks into a island!\r\n");
			result_flag = -1;
		}
	}

	// 定位尚未有归属的内流区到某一个岛屿
	for (i = 1; i <= sink_num; i++) {
		if (merge_flag[i] == 0) {
			merge_flag[i] = mArray[union_flag[i]];
		}
	}

	// 释放内存
	free(mArray);
	u8_VLArray2D_Destroy(utMatrix, sink_num + 1);


	if (result_flag < 0) {
		region_id = result_flag;
	}
	return region_id;
}



uint8_t _find_attached_basin_uint8(uint64_t* __restrict sink_idxs, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, int32_t rows, int32_t cols) {


	uint64_t cols64 = (uint64_t)cols;
	double frac = 0.1;
	uint64_t STACK_SIZE = ((uint64_t)(rows * cols64 * frac / 10000) + 1) * 10000;

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);
	
	uint8_t result = _find_attached_basin_uint8_core(sink_idxs, sink_num, re_dir, elv, basin, stack, offset, div);

	u64_DynArray_Destroy(stack);

	return result;
}


uint8_t _find_attached_basin_uint8_core(uint64_t* __restrict sink_idxs, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, u64_DynArray* stack, const int32_t* offset, const uint8_t* div) {

	uint64_t idx = 0, upper_idx = 0;
	int32_t i = 0, p = 0;
	uint8_t reverse_dir = 0;
	uint8_t ridge_flag = 0;
	uint8_t attached_basin = 0;
	float lowest_elv = 9999.f;

	// loop each sink, find lowest pass to a coded basin
	for (i = 0; i < sink_num; i++) {
		// reset stack
		stack->length = 0;
		// Push sink bottom into stack
		u64_DynArray_Push(stack, sink_idxs[i]);
		// Loop all pixels of sink
		while (stack->length > 0) {
			// Pop an element
			idx = stack->data[--stack->length];
			reverse_dir = re_dir[idx];
			ridge_flag = 0;

			// Loop 8 neighbours
			for (p = 0; p < 8; p++) {
				// Find a upstream pixel
				if (reverse_dir >= div[p]) {
					upper_idx = idx + offset[p];
					u64_DynArray_Push(stack, upper_idx);
					reverse_dir -= div[p];
					++ridge_flag;
				}
			}
			// Try to find a lowest pass to coded basins 
			if (ridge_flag == 0) {
				for (p = 1; p < 8; p += 2) {
					upper_idx = idx + offset[p];
					if (basin[upper_idx] > 0 && elv[upper_idx] < lowest_elv) {
						attached_basin = basin[upper_idx];
						lowest_elv = elv[upper_idx];
					}
				}
			}
		}
	}

	return attached_basin;
}









uint8_t _region_decompose_uint8(uint64_t* __restrict sink_idxs, float* __restrict sink_areas, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, int32_t rows, int32_t cols) {

	// 单一变量
	int32_t i, j;
	uint8_t expected_num = 10;
	float total_area = 0.f;
	double frac = 0.1;

	// 数组变量
	uint8_t* region_flag = u8_VLArray_Initial(sink_num, 1);
	int32_t* sink_envelopes = i32_VLArray_Initial(4 * (sink_num + 1), 1);
	int32_t* dstFromCorener = i32_VLArray_Initial(sink_num, 0);
	int32_t* i32_basin = i32_VLArray_Initial(rows * (uint64_t)cols, 1);

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	uint64_t STACK_SIZE = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	// 先统计当前内流区的总面积,绘制每一个内流区
	for (i = 0; i < sink_num; i++) {
		total_area += sink_areas[i];
		_paint_upper_int32(sink_idxs[i], i + 1, stack, i32_basin, re_dir, offset, div);
	}

	// 创建内流流域邻接矩阵
	uint8_t** adjacentMatrix = _create_sink_adjacentMatrix(sink_num, i32_basin, rows, cols);

	// 计算每个内流流域的外包矩形
	for (i = 0; i <= sink_num; i++) {
		sink_envelopes[4 * i] = rows;
		sink_envelopes[4 * i + 1] = cols;
	}
	_get_basin_envelope_int32(i32_basin, sink_envelopes, rows, cols);

	// 计算每个内流区外包矩形左上角到整幅影像左上角的距离
	for (i = 0; i < sink_num; i++) {
		dstFromCorener[i] = sink_envelopes[4 * i + 5];
	}

	// 划分内流区 
	uint8_t result = _region_decompose_uint8_core(sink_areas, sink_num, total_area, expected_num, region_flag, dstFromCorener, adjacentMatrix);
	free(sink_envelopes);
	free(dstFromCorener);
	free(i32_basin);

	// 为剩余的内流流域分配编码
	i32_DynArray* other_sinks = i32_DynArray_Initial(sink_num);
	for (i = 0; i < sink_num; i++) {
		if (region_flag[i] == 0) {
			i32_DynArray_Push(other_sinks, i);
		}
		else {
			_paint_upper_uint8(sink_idxs[i], region_flag[i], stack, basin, re_dir, offset, div);
		}
	}

	uint64_t* s_sink_idxs = u64_VLArray_Initial(1, 0);
	uint8_t flag = 0;
	uint8_t attached_basin = 0;
	int32_t sink_id, other_sink_id;

	while (other_sinks->length > 0) {
		for (i = other_sinks->length - 1; i >= 0; i--) {
			sink_id = other_sinks->data[i];
			flag = 0;
			for (other_sink_id = 0; other_sink_id < sink_num; other_sink_id++) {
				if (region_flag[other_sink_id] != 0) {
					if (adjacentMatrix[sink_id + 1][other_sink_id + 1] == 1 || 
						adjacentMatrix[other_sink_id + 1][sink_id + 1] == 1) {
						flag = 1;
						break;
					}
				}
			}
			if (flag == 1) {
				s_sink_idxs[0] = sink_idxs[sink_id];
				attached_basin = _find_attached_basin_uint8_core(s_sink_idxs, 1, re_dir, elv, basin, stack, offset, div);
				region_flag[sink_id] = attached_basin;
				_paint_upper_uint8(s_sink_idxs[0], attached_basin, stack, basin, re_dir, offset, div);
				for (j = i; j < other_sinks->length - 1; j++) {
					other_sinks->data[j] = other_sinks->data[j + 1];
				}
				other_sinks->length--;
			}
		}
	}

	free(s_sink_idxs);
	i32_DynArray_Destroy(other_sinks);
	u8_VLArray2D_Destroy(adjacentMatrix, sink_num + 1);
	u64_DynArray_Destroy(stack);
	free(region_flag);

	return result;
}


uint8_t** _create_sink_adjacentMatrix(int32_t sink_num, int32_t* __restrict basin, int rows, int cols) {

	// 开辟上三角矩阵，存储内流区的相邻信息
	uint8_t** utMatrix = u8_VLArray2D_Initial(sink_num + 1, sink_num + 1, 1);

	uint64_t cols64 = (uint64_t)cols;
	uint64_t idx = cols64 + 1;
	int32_t i, j, src_value, value;
	for (i = 1; i < rows - 1; i++) {
		for (j = 1; j < cols - 1; j++) {
			src_value = basin[idx];
			// 如果是内流区像元,判断四邻域范围内是否有其他内流区或外流区
			if (src_value > 0) {
				// right pixel
				value = basin[idx + 1];
				if (value == 0 || value == src_value) {
					;
				}
				else {
					utMatrix[src_value][value] = 1;
				}
				// down pixel
				value = basin[idx + cols64];
				if (value == 0 || value == src_value) {
					;
				}
				else {
					utMatrix[src_value][value] = 1;
				}
			}
			++idx;
		}
		idx += 2;
	}

	return utMatrix;
}


int32_t _region_decompose_uint8_core(float* __restrict sink_areas, int32_t sink_num, float total_area, uint8_t expected_num, 
	uint8_t* __restrict region_flag, int32_t* __restrict dstFromCorner, uint8_t** __restrict adjacentMatrix) {


	float expected_area = total_area / expected_num;
	float cur_area = 0.f;
	uint8_t sub_num = 0;
	int32_t sink_id, nb_sink_id;
	i32_DynArray* neighbours = i32_DynArray_Initial(sink_num);

	while (sub_num < expected_num) {
		cur_area = 0.f;
		neighbours->length = 0;
		sub_num++;
		sink_id = _find_a_corner_sink(sink_num, region_flag, dstFromCorner);
		if (sink_id == -1) {
			break;
		}
		do {
			region_flag[sink_id] = sub_num;
			cur_area += sink_areas[sink_id];
			// 加入sink_id 的邻居
			for (nb_sink_id = 0; nb_sink_id < sink_num; nb_sink_id++) {
				if (region_flag[nb_sink_id] == 0) {
					if (adjacentMatrix[sink_id + 1][nb_sink_id + 1] == 1 ||
						adjacentMatrix[nb_sink_id + 1][sink_id + 1] == 1) {
						if (!check_in_i32_DynArray(nb_sink_id, neighbours)) {
							i32_DynArray_Push(neighbours, nb_sink_id);
						}
					}
				}
			}
			sink_id = _find_a_corner_sink_from_neighbours(sink_areas, sink_num, expected_area - cur_area, neighbours, dstFromCorner);
		} while (sink_id != -1);
	}

	i32_DynArray_Destroy(neighbours);
	return sub_num;
}


int32_t _find_a_corner_sink(int32_t sink_num, uint8_t* __restrict region_flag, int32_t* __restrict dstFromCorner) {

	int32_t result = -1;
	int32_t min_dst = INT32_MAX;

	for (int32_t i = 0; i < sink_num; i++) {
		if (region_flag[i] == 0) {
			if (dstFromCorner[i] < min_dst) {
				result = i;
				min_dst = dstFromCorner[i];
			}
		}
	}
	return result;
}


int32_t _find_a_corner_sink_from_neighbours(float* __restrict sink_areas, int32_t sink_num, float left_area, 
	i32_DynArray* __restrict nbs, int32_t* __restrict dstFromCorner) {

	int32_t result = -1, pop_idx = -1;
	int32_t min_dst = INT32_MAX;
	int32_t sink_id;

	for (int32_t i = 0; i < nbs->length; i++) {
		sink_id = nbs->data[i];
		if (sink_areas[sink_id] <= left_area) {
			if (dstFromCorner[sink_id] < min_dst) {
				result = sink_id;
				min_dst = dstFromCorner[sink_id];
				pop_idx = i;
			}
		}
	}

	if (pop_idx != -1) {
		for (; pop_idx < nbs->length - 1; pop_idx++) {
			nbs->data[pop_idx] = nbs->data[pop_idx + 1];
		}
		nbs->length--;
	}

	return result;
}





uint8_t _region_decompose_uint8_2(uint64_t* __restrict sink_idxs, float* __restrict sink_areas, int32_t sink_num, uint8_t* __restrict re_dir,
	float* __restrict elv, uint8_t* __restrict basin, int32_t rows, int32_t cols) {

	// 单一变量
	int32_t i, j;
	uint8_t expected_num = 10;
	uint8_t result = 0;
	float total_area = 0.f;
	double frac = 0.1;

	// 数组变量
	uint8_t* region_flag = u8_VLArray_Initial(sink_num, 1);
	int32_t* sink_envelopes = i32_VLArray_Initial(4 * (sink_num + 1), 1);
	int32_t* dstFromCorener = i32_VLArray_Initial(sink_num, 0);
	int32_t* i32_basin = i32_VLArray_Initial(rows * (uint64_t)cols, 1);

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	uint64_t STACK_SIZE = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	// 先统计当前内流区的总面积,绘制每一个内流区
	for (i = 0; i < sink_num; i++) {
		total_area += sink_areas[i];
		_paint_upper_int32(sink_idxs[i], i + 1, stack, i32_basin, re_dir, offset, div);
	}

	// 创建内流流域邻接矩阵
	uint8_t** adjacentMatrix = _create_sink_adjacentMatrix(sink_num, i32_basin, rows, cols);

	// 计算每个内流流域的外包矩形
	for (i = 0; i <= sink_num; i++) {
		sink_envelopes[4 * i] = rows;
		sink_envelopes[4 * i + 1] = cols;
	}
	_get_basin_envelope_int32(i32_basin, sink_envelopes, rows, cols);
	free(i32_basin);
	// 计算每个内流区外包矩形左上角到整幅影像左上角的距离
	for (i = 0; i < sink_num; i++) {
		dstFromCorener[i] = sink_envelopes[4 * i + 4] + sink_envelopes[4 * i + 5];
	}
	free(sink_envelopes);
	
	// 划分内流区
	int32_t* sink_ids = i32_VLArray_Initial(sink_num, 0);
	for (i = 0; i < sink_num; i++) {
		sink_ids[i] = i;
	}
	result = _region_decompose_uint8_core_2(sink_ids, sink_num, total_area, expected_num, result, sink_areas, region_flag, dstFromCorener, adjacentMatrix);
	free(dstFromCorener);
	free(sink_ids);

	// 为剩余的内流流域分配编码
	i32_DynArray* other_sinks = i32_DynArray_Initial(sink_num);
	for (i = 0; i < sink_num; i++) {
		if (region_flag[i] == 0) {
			i32_DynArray_Push(other_sinks, i);
		}
		else {
			_paint_upper_uint8(sink_idxs[i], region_flag[i], stack, basin, re_dir, offset, div);
		}
	}

	uint64_t* s_sink_idxs = u64_VLArray_Initial(1, 0);
	uint8_t flag = 0;
	uint8_t attached_basin = 0;
	int32_t sink_id, other_sink_id;

	while (other_sinks->length > 0) {
		for (i = other_sinks->length - 1; i >= 0; i--) {
			sink_id = other_sinks->data[i];
			flag = 0;
			for (other_sink_id = 0; other_sink_id < sink_num; other_sink_id++) {
				if (region_flag[other_sink_id] != 0) {
					if (adjacentMatrix[sink_id + 1][other_sink_id + 1] == 1 ||
						adjacentMatrix[other_sink_id + 1][sink_id + 1] == 1) {
						flag = 1;
						break;
					}
				}
			}
			if (flag == 1) {
				s_sink_idxs[0] = sink_idxs[sink_id];
				attached_basin = _find_attached_basin_uint8_core(s_sink_idxs, 1, re_dir, elv, basin, stack, offset, div);
				region_flag[sink_id] = attached_basin;
				_paint_upper_uint8(s_sink_idxs[0], attached_basin, stack, basin, re_dir, offset, div);
				for (j = i; j < other_sinks->length - 1; j++) {
					other_sinks->data[j] = other_sinks->data[j + 1];
				}
				other_sinks->length--;
			}
		}
	}

	free(s_sink_idxs);
	i32_DynArray_Destroy(other_sinks);
	u8_VLArray2D_Destroy(adjacentMatrix, sink_num + 1);
	u64_DynArray_Destroy(stack);
	free(region_flag);

	return result;
}





uint8_t _region_decompose_uint8_core_2(int32_t* __restrict cur_sinks, int32_t cur_sink_num, float cur_total_area, uint8_t cur_expected_num, uint8_t sub_num,
	float* __restrict sink_areas, uint8_t* __restrict region_flag, int32_t* __restrict dstFromCorner, uint8_t** __restrict adjacentMatrix) {

	int32_t i, j, sink_id;
	uint8_t cur_max_num = cur_expected_num + sub_num;
	float left_area = cur_total_area;
	// 如果当前内流区不进行划分
	if (cur_expected_num == 1) {
		sub_num++;
		for (i = 0; i < cur_sink_num; i++) {
			sink_id = cur_sinks[i];
			region_flag[sink_id] = sub_num;
		}
		return sub_num;
	}
	
	// 先统计当前的期望面积
	float cur_expected_area = cur_total_area / cur_expected_num;
	// 找出大于平均期望面积的内流流域,这些流域不会与其他流域合并
	for (i = 0; i < cur_sink_num; i++) {
		sink_id = cur_sinks[i];
		if (sink_areas[sink_id] < cur_expected_area) {
			break;
		}
		sub_num++;
		region_flag[sink_id] = sub_num;
		left_area -= sink_areas[sink_id];
	}

	// 如果大于平均期望面积的内流流域
	if (cur_max_num == (cur_expected_num + sub_num)) {
		float sub_area = 0.f;
		int32_t nb_sink_id;
		i32_DynArray* neighbours = i32_DynArray_Initial(cur_sink_num);
		sink_id = _find_a_corner_sink_2(cur_sinks, cur_sink_num, region_flag, dstFromCorner);
		sub_num++;
		do {
			region_flag[sink_id] = sub_num;
			sub_area += sink_areas[sink_id];
			// 加入sink_id 的邻居
			for (i = 0; i < cur_sink_num; i++) {
				nb_sink_id = cur_sinks[i];
				if (region_flag[nb_sink_id] == 0) {
					if (adjacentMatrix[sink_id + 1][nb_sink_id + 1] == 1 ||
						adjacentMatrix[nb_sink_id + 1][sink_id + 1] == 1) {
						if (!check_in_i32_DynArray(nb_sink_id, neighbours)) {
							i32_DynArray_Push(neighbours, nb_sink_id);
						}
					}
				}
			}
			sink_id = _find_a_corner_sink_from_neighbours_2(cur_expected_area - sub_area, sink_areas, neighbours, dstFromCorner);
		} while (sink_id != -1);
		i32_DynArray_Destroy(neighbours);
		left_area -= sub_area;
	}

	int32_t sub_region_num = 0;
	i32_DynArray** sub_regions = _get_sub_regions_2(cur_sinks, cur_sink_num, &sub_region_num, adjacentMatrix, region_flag);
	// 统计内流区面积
	float* sub_region_areas = (float*)calloc(sub_region_num, sizeof(float));
	if (sub_region_areas == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (i = 0; i < sub_region_num; i++) {
		for (j = 0; j < sub_regions[i]->length; j++) {
			sub_region_areas[i] += sink_areas[sub_regions[i]->data[j]];
		}
	}

	// 对次生内流区按面积排序
	int32_t* sub_region_orders = _argqsort_float(sub_region_areas, sub_region_num);
	int32_t region_id = 0;
	uint8_t sub_expected_num = 0;
	uint8_t left_num = cur_max_num - sub_num;
	float region_area = 0.f;
	float sub_expected_area = left_area / (cur_max_num - sub_num);

	for (i = sub_region_num - 1; i >= 0; i--) {
		region_id = sub_region_orders[i];
		region_area = sub_region_areas[region_id];
		if (region_area > (1.5 * sub_expected_area)) {
			sub_expected_num = (uint8_t)((region_area - 0.5 * sub_expected_area) / sub_expected_area) + 1;
			sub_expected_num = min(left_num, sub_expected_num);
			sub_num =_region_decompose_uint8_core_2(sub_regions[region_id]->data, sub_regions[region_id]->length, region_area, sub_expected_num, sub_num,
				sink_areas, region_flag, dstFromCorner, adjacentMatrix);
		}
		else {
			sub_expected_num = 1;
			sub_num = _region_decompose_uint8_core_2(sub_regions[region_id]->data, sub_regions[region_id]->length, region_area, sub_expected_num, sub_num,
				sink_areas, region_flag, dstFromCorner, adjacentMatrix);
		}
		left_num -= sub_expected_num;
		if (left_num <= 0) {
			break;
		}
	}

	for (i = 0; i < sub_region_num; i++) {
		i32_DynArray_Destroy(sub_regions[i]);
	}
	free(sub_regions);
	free(sub_region_orders);
	free(sub_region_areas);
	return sub_num;
}


i32_DynArray** _get_sub_regions_2(int32_t* __restrict cur_sinks, int32_t cur_sink_num, int* region_num, uint8_t** __restrict adjacentMatrix, uint8_t* __restrict region_flag) {

	// 辅助变量
	int32_t i, j, m, n, l, sink_id, nb_sink_id;
	int32_t region_id = 0;

	// 计算次级内流区
	int32_t* cur_region_flag = i32_VLArray_Initial(cur_sink_num + 1, 1);
	for (i = 1; i <= cur_sink_num; i++) {
		sink_id = cur_sinks[i - 1];
		if (region_flag[sink_id] != 0) {
			continue;
		}
		for (j = i + 1; j <= cur_sink_num; j++) {
			nb_sink_id = cur_sinks[j - 1];
			if (region_flag[nb_sink_id] != 0) {
				continue;
			}
			if (adjacentMatrix[sink_id + 1][nb_sink_id + 1] == 1 || 
				adjacentMatrix[nb_sink_id + 1][sink_id + 1] == 1) {
				m = i;
				n = j;
				while ((cur_region_flag[n] != 0) && (cur_region_flag[n] != m)) {
					l = cur_region_flag[n];
					if (cur_region_flag[n] < m) {
						n = m;
						m = l;
					}
					else {
						cur_region_flag[n] = m;
						n = l;
					}
				}
				if (cur_region_flag[n] == 0) {
					cur_region_flag[n] = m;
				}
			}
		}
	}

	for (i = 1; i <= cur_sink_num; i++) {
		sink_id = cur_sinks[i - 1];
		if (region_flag[sink_id] == 0) {
			if (cur_region_flag[i] == 0) {
				cur_region_flag[i] = ++region_id;
			}
			else {
				cur_region_flag[i] = cur_region_flag[cur_region_flag[i]];
			}
		}
	}

	// 次级内流区由哪些流域组成
	int32_t cur_region_num = region_id;
	i32_DynArray** sub_regions = (i32_DynArray**)malloc(cur_region_num * sizeof(i32_DynArray*));
	if (sub_regions == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (i = 0; i < cur_region_num; i++) {
		sub_regions[i] = i32_DynArray_Initial(cur_sink_num);
	}


	for (i = 1; i <= cur_sink_num; i++) {
		sink_id = cur_sinks[i - 1];
		region_id = cur_region_flag[i];
		if (region_id > 0) {
			i32_DynArray_Push(sub_regions[region_id - 1], sink_id);
		}
	}
	// 释放内存
	free(cur_region_flag);
	*region_num = cur_region_num;
	return sub_regions;
}


int32_t _find_a_corner_sink_2(int32_t* __restrict cur_sinks, int32_t cur_sink_num, uint8_t* __restrict region_flag, int32_t* __restrict dstFromCorner) {

	int32_t result = -1;
	int32_t min_dst = INT32_MAX;
	int32_t sink_id;

	for (int32_t i = 0; i < cur_sink_num; i++) {
		sink_id = cur_sinks[i];
		if (region_flag[sink_id] == 0) {
			if (dstFromCorner[sink_id] < min_dst) {
				result = sink_id;
				min_dst = dstFromCorner[sink_id];
			}
		}
	}
	return result;
}


int32_t _find_a_corner_sink_from_neighbours_2(float left_area, float* __restrict sink_areas, i32_DynArray* __restrict nbs, int32_t* __restrict dstFromCorner) {

	int32_t result = -1, pop_idx = -1;
	int32_t min_dst = INT32_MAX;
	int32_t sink_id;

	for (int32_t i = 0; i < nbs->length; i++) {
		sink_id = nbs->data[i];
		if (sink_areas[sink_id] <= left_area) {
			if (dstFromCorner[sink_id] < min_dst) {
				result = sink_id;
				min_dst = dstFromCorner[sink_id];
				pop_idx = i;
			}
		}
	}

	if (pop_idx != -1) {
		for (; pop_idx < nbs->length - 1; pop_idx++) {
			nbs->data[pop_idx] = nbs->data[pop_idx + 1];
		}
		nbs->length--;
	}

	return result;
}


int32_t _sink_region(uint64_t* __restrict sink_idxs, float* __restrict sink_areas, int32_t sink_num, 
	uint8_t* __restrict dir, int32_t rows, int32_t cols, int32_t* __restrict region_flag) {

	int32_t i, j, m, n, l;
	float total_area = 0.f;
	double frac = 0.1;

	// 数组变量
	int32_t* i32_basin = i32_VLArray_Initial(rows * (uint64_t)cols, 1);

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	uint64_t STACK_SIZE = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	u64_DynArray* stack = u64_DynArray_Initial(STACK_SIZE);

	uint8_t* re_dir = _get_re_dir(dir, rows, cols);

	// 先统计当前内流区的总面积,绘制每一个内流区
	for (i = 0; i < sink_num; i++) {
		total_area += sink_areas[i];
		_paint_upper_int32(sink_idxs[i], i + 1, stack, i32_basin, re_dir, offset, div);
	}
	free(re_dir);
	u64_DynArray_Destroy(stack);
	// 创建内流流域邻接矩阵
	uint8_t** adjacentMatrix = _create_sink_adjacentMatrix(sink_num, i32_basin, rows, cols);
	free(i32_basin);


	for (i = 1; i <= sink_num; i++) {
		for (j = i + 1; j <= sink_num; j++) {
			if (adjacentMatrix[i][j] == 1 ||
				adjacentMatrix[j][i] == 1) {
				m = i;
				n = j;
				while ((region_flag[n] != 0) && (region_flag[n] != m)) {
					l = region_flag[n];
					if (region_flag[n] < m) {
						n = m;
						m = l;
					}
					else {
						region_flag[n] = m;
						n = l;
					}
				}
				if (region_flag[n] == 0) {
					region_flag[n] = m;
				}
			}
		}
	}

	int32_t region_id = 0;
	for (i = 1; i <= sink_num; i++) {
		if (region_flag[i] == 0) {
			region_flag[i] = ++region_id;
		}
		else {
			region_flag[i] = region_flag[region_flag[i]];
		}
	}

	int32_t region_num = region_id;
	// 统计内流区面积
	float* region_areas = (float*)calloc(region_num, sizeof(float));
	if (region_areas == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (i = 1; i <= sink_num; i++) {
		region_id = region_flag[i];
		region_areas[region_id - 1] += sink_areas[i - 1];
	}

	// 对次生内流区按面积排序
	int32_t new_region_id;
	int32_t* region_orders = _argqsort_float(region_areas, region_num);
	for (i = 1; i <= sink_num; i++) {
		region_id = region_flag[i];
		new_region_id = region_num - region_orders[region_id - 1];
		region_flag[i] = new_region_id;
	}

	free(region_orders);
	free(region_areas);
	u8_VLArray2D_Destroy(adjacentMatrix, sink_num + 1);

	return region_num;
}