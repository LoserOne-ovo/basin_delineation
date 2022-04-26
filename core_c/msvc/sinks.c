#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "sinks.h"


int _dissolve_sinks_uint16(unsigned short* __restrict basin, unsigned char* __restrict re_dir, float* __restrict dem, 
	unsigned long long* __restrict sink_idxs, unsigned short sink_num, int rows, int cols, double frac) {


	uint64 idx = 0;
	uint64 cols64 = (uint64)cols;
	// 根据提供的比例，计算需要用到的栈深度（不要在意用quene命名栈）
	uint64 QUENE_SIZE = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (QUENE_SIZE > 100000000) {
		QUENE_SIZE = 100000000;
	}
	uint64 RC_SIZE = 10000;
	uint16 min_sink = 11;
	uint16* __restrict colors = (uint16*)calloc(sink_num, sizeof(unsigned short));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint16 i = 0; i < sink_num; i++) {
		colors[i] = min_sink + i;
	}

	// 存储每一个内流区的边界像元
	u64_List* rim_cell = (u64_List*)calloc(sink_num, sizeof(u64_List));
	if (rim_cell == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint16 i = 0; i < sink_num; i++) {
		rim_cell[i].batch_size = RC_SIZE;
		rim_cell[i].List = (uint64*)calloc(RC_SIZE, sizeof(uint64));
		if (rim_cell[i].List == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}
		rim_cell[i].alloc_length = RC_SIZE;
		rim_cell[i].length = 0;
	}

	// 初始化上游追踪需要的辅助数据
	uint8 reverse_fdir = 0;
	uint16 color = 0;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_List quene = { 0,0,QUENE_SIZE,NULL };

	// 用于存储上游像元的栈
	quene.List = (uint64*)calloc(QUENE_SIZE, sizeof(uint64));
	if (quene.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	quene.alloc_length = QUENE_SIZE;

	// 循环绘制每一个内流区
	for (uint16 i = 0; i < sink_num; i++) {

		// 读取内流区的绘图颜色信息
		color = colors[i];
		// 在不重新分配内存的情况下，清空栈，并压入内流区终点的位置索引
		quene.List[0] = sink_idxs[i];
		quene.length = 1;

		while (quene.length > 0) {
			idx = quene.List[quene.length - 1];
			basin[idx] = color;
			quene.length--;
			reverse_fdir = re_dir[idx];

			// 在追溯的过程中，如果一个像元没有上游，那么就认为是边界像元
			if (reverse_fdir == 0) {
				u64_List_append(&rim_cell[i], idx);
			}
			// 如果有上游，则进行绘制
			else {
				for (int p = 0; p < 8; p++) {
					if (reverse_fdir >= div[p]) {
						u64_List_append(&quene, idx + offset[p]);
						reverse_fdir -= div[p];
					}
				}
			}
		}
	}

	// 将内流域合并到外流区，以外流区编号记录下合并结果
	uint16* merge_flag = _inner_merge_u16(basin, dem, rim_cell, sink_num, min_sink, offset);

	for (uint16 i = 0; i < sink_num;i++) {
		free(rim_cell[i].List);
	}
	free(rim_cell);
	rim_cell = NULL;


	// 以新的编号重新追溯上游
	for (uint16 i = 0;i < sink_num; i++) {

		idx = sink_idxs[i];
		color = merge_flag[i];
		quene.List[0] = idx;
		quene.length = 1;

		while (quene.length > 0) {
			idx = quene.List[quene.length - 1];
			basin[idx] = color;
			quene.length--;
			reverse_fdir = re_dir[idx];

			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_List_append(&quene, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
		}
	}

	free(quene.List);
	free(merge_flag);
	free(colors);

	return 1;
}



unsigned short* _inner_merge_u16(unsigned short* __restrict basin, float* __restrict elev, u64_List* rim_cell, unsigned short sink_num, unsigned short min_sink, const int offset[])
{
	// 函数的返回结果，用于存储内流区被合并到哪个流域
	uint16* merge_flag = (uint16*)calloc(sink_num, sizeof(uint16));
	if (merge_flag == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	
	// 初始化辅助参数
	uint64 CB_SIZE = 100;
	uint16 wrong_tag = 10000;
	uint16 next_basin = 0;
	u64_List* temp;

	// 记录当前要处理的流域编号（一个内流区可能合并到另一个内流区），用于去除非边界像元
	u16_List* cur_basin = (u16_List*)malloc(sizeof(u16_List));
	if (cur_basin == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	cur_basin->batch_size = CB_SIZE;
	cur_basin->List = (uint16*)calloc(CB_SIZE, sizeof(uint16));
	if (cur_basin->List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	cur_basin->alloc_length = CB_SIZE;
	cur_basin->List[0] = 0; // 第一位存储0，保证流域不被合并到数据范围之外
	cur_basin->length = 1;


	for (uint16 i = 0; i < sink_num; i++) {

		// 尚未被合并
		if (merge_flag[i] == 0) {
			// 加入到当前待处理流域列表中
			u16_List_append(cur_basin, min_sink + i);
			// 去除流域内部的局部最高点
			temp = _remove_inner_peak_u16(&rim_cell[i], basin, cur_basin, offset);
			
			// 错误情况：没有流域边界像元
			if (temp->length == 0) {
				// 给予该流域一个错误编号
				merge_flag[i] = wrong_tag++;
				// 重设辅助数据，并处理下一个流域
				cur_basin->length = 1;
				free(temp->List);
				free(temp);
				continue;
			}
			// 寻找合并到的下一个流域
			next_basin = _find_next_basin_u16(temp, elev, basin, cur_basin, offset);
			
			// 如果流域没有合并的外流区
			while (next_basin >= min_sink) {
				
				// 如果合并到一个没有处理过的内流区，继续合并
				if (merge_flag[next_basin - min_sink] == 0) {
					u16_List_append(cur_basin, next_basin);
					// 重新寻找流域边界和要合并到的流域
					temp = _eL_merge_u16(temp, &rim_cell[next_basin - min_sink], basin, cur_basin, offset);
					next_basin = _find_next_basin_u16(temp, elev, basin, cur_basin, offset);
				}
				// 如果合并到已经处理过的内流区，停止合并
				else {
					break;
				}
			}

			// 没有边界像元的错误情况
			if (next_basin == 0) {
				for (uint q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->List[q] - min_sink] = wrong_tag;
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
				for (uint q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->List[q] - min_sink] = next_basin;
				}

			}
			cur_basin->length = 1;
			free(temp->List);
			free(temp);
		}
	}

	free(cur_basin->List);
	free(cur_basin);

	return merge_flag;
}



// 将流域内部的局部最高点和被海洋包围的边界点，从边界像元中除去
u64_List* _remove_inner_peak_u16(u64_List* src, unsigned short* basin, u16_List* cur_color, const int offset[]) {
	
	
	register uint64 idx = 0;
	u64_List* res = (u64_List*)malloc(sizeof(u64_List));
	if (res == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->List = (uint64*)calloc(src->length, sizeof(uint64));
	if (res->List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->batch_size = src->batch_size;
	res->alloc_length = src->length;

	for (uint i = 0; i < src->length; i++) {
		for (int j = 0; j < 8; j++) {
			idx = src->List[i] + offset[j];
			if (!check_in_u16_List(basin[idx], cur_color)) {
				res->List[res->length++] = src->List[i];
				break;
			}
		}
	}

	return res;
}



//将两个流域的边界像元进行组合，需要重复remove_inner_peak操作
u64_List* _eL_merge_u16(u64_List* __restrict src, u64_List* __restrict ins, unsigned short* basin, u16_List* cur_basin, const int offset[]){

	uint64 idx = 0;
	uint64 all_length = src->length + ins->length;
	
	u64_List* res = (u64_List*)malloc(sizeof(u64_List));
	if (res == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->batch_size = src->batch_size;
	res->List = (uint64*)calloc(all_length, sizeof(uint64));
	if (res->List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->alloc_length = all_length;
	
	for (uint i = 0; i < src->length; i++) {
		for (int j = 0; j < 8; j++) {
			idx = src->List[i] + offset[j];
			if (!check_in_u16_List(basin[idx], cur_basin)) {
				res->List[res->length++] = src->List[i];
				break;
			}
		}
	}
	
	for (uint i = 0; i < ins->length; i++) {
		for (int j = 0; j < 8; j++) {
			idx = ins->List[i] + offset[j];
			if (!check_in_u16_List(basin[idx], cur_basin)) {
				res->List[res->length++] = ins->List[i];
				break;
			}
		}
	}
	
	free(src->List);
	free(src);
	src = NULL;

	return res;
}


unsigned short _find_next_basin_u16(u64_List* edge_list, float* elev, unsigned short* basin, u16_List* cur_basin, const int offset[]) {

	// 初始化参数
	uint16 next_basin = 0;
	float min_elev = 9999;
	float max_elev_diff = -9999, temp_elev_diff = 0;
	uint64 min_idx = 0, temp_idx = 0;

	if (edge_list->length > 0) {
		// 先找到边界上的最低点
		for (uint i = 0; i < edge_list->length;i++) {
			if (elev[edge_list->List[i]] < min_elev) {
				min_idx = edge_list->List[i];
				min_elev = elev[min_idx];
			}
		}
		// 再找高差最大的方向
		for (int i = 0; i < 8; i++) {
			temp_idx = min_idx + offset[i];
			temp_elev_diff = elev[min_idx] - elev[temp_idx];
			if ((temp_elev_diff > max_elev_diff) &&
				!(check_in_u16_List(basin[temp_idx], cur_basin))) {
				next_basin = basin[temp_idx];
				max_elev_diff = temp_elev_diff;
			}
		}
	}
	// 在没有边界像元的情况下返回0
	// 正常情况返回要合并入的流域的编号
	return next_basin;
}






int _dissolve_sinks_uint8(unsigned char* __restrict basin, unsigned char* __restrict re_dir, float* __restrict dem, 
	unsigned long long* __restrict sink_idxs, unsigned char sink_num, int rows, int cols, double frac) {

	uint64 idx = 0;
	uint64 cols64 = (uint64)cols;
	// 根据提供的比例，计算需要用到的栈深度（不要在意用quene命名栈）
	uint64 QUENE_SIZE = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (QUENE_SIZE > 100000000) {
		QUENE_SIZE = 100000000;
	}
	// 假定的内流区边界像元数量
	uint64 RC_SIZE = 10000;

	uint8 min_sink = 11;
	uint8* __restrict colors = (uint8*)calloc(sink_num, sizeof(unsigned char));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint8 i = 0; i < sink_num; i++) {
		colors[i] = min_sink + i;
	}

	// 存储每一个内流区的边界像元
	u64_List* rim_cell = (u64_List*)calloc(sink_num, sizeof(u64_List));
	if (rim_cell == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint8 i = 0; i < sink_num; i++) {
		rim_cell[i].batch_size = RC_SIZE;
		rim_cell[i].List = (uint64*)calloc(RC_SIZE, sizeof(uint64));
		if (rim_cell[i].List == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}
		rim_cell[i].alloc_length = RC_SIZE;
		rim_cell[i].length = 0;
	}

	// 初始化上游追踪需要的辅助数据
	uint8 reverse_fdir = 0;
	uint8 color = 0;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_List quene = { 0,0,QUENE_SIZE,NULL };

	// 用于存储上游像元的栈
	quene.List = (uint64*)calloc(QUENE_SIZE, sizeof(uint64));
	if (quene.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	quene.alloc_length = QUENE_SIZE;

	// 循环绘制每一个内流区
	for (uint8 i = 0; i < sink_num; i++) {

		// 读取内流区的绘图颜色信息
		color = colors[i];
		// 在不重新分配内存的情况下，清空栈，并压入内流区终点的位置索引
		quene.List[0] = sink_idxs[i];
		quene.length = 1;

		while (quene.length > 0) {
			idx = quene.List[quene.length - 1];
			basin[idx] = color;
			quene.length--;
			reverse_fdir = re_dir[idx];

			// 在追溯的过程中，如果一个像元没有上游，那么就认为是边界像元
			if (reverse_fdir == 0) {
				u64_List_append(&rim_cell[i], idx);
			}
			// 如果有上游，则进行绘制
			else {
				for (int p = 0; p < 8; p++) {
					if (reverse_fdir >= div[p]) {
						u64_List_append(&quene, idx + offset[p]);
						reverse_fdir -= div[p];
					}
				}
			}
		}
	}

	// 将内流域合并到外流区，以外流区编号记录下合并结果
	uint8* merge_flag = _inner_merge_u8(basin, dem, rim_cell, sink_num, min_sink, offset);

	for (uint8 i = 0; i < sink_num;i++) {
		free(rim_cell[i].List);
	}
	free(rim_cell);
	rim_cell = NULL;


	// 以新的编号重新追溯上游
	for (uint8 i = 0;i < sink_num; i++) {

		idx = sink_idxs[i];
		color = merge_flag[i];
		quene.List[0] = idx;
		quene.length = 1;

		while (quene.length > 0) {
			idx = quene.List[quene.length - 1];
			basin[idx] = color;
			quene.length--;
			reverse_fdir = re_dir[idx];

			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_List_append(&quene, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
		}
	}

	free(quene.List);
	free(merge_flag);
	free(colors);

	return 1;
}



unsigned char* _inner_merge_u8(unsigned char* __restrict basin, float* __restrict elev, u64_List* rim_cell, unsigned char sink_num, unsigned char min_sink, const int offset[])
{
	// 函数的返回结果，用于存储内流区被合并到哪个流域
	uint8* merge_flag = (uint8*)calloc(sink_num, sizeof(uint8));
	if (merge_flag == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// 初始化辅助参数
	uint64 CB_SIZE = 100;
	uint8 wrong_tag = 100;
	uint8 next_basin = 0;
	u64_List* temp;

	// 记录当前要处理的流域编号（一个内流区可能合并到另一个内流区），用于去除非边界像元
	u8_List* cur_basin = (u8_List*)malloc(sizeof(u8_List));
	if (cur_basin == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	cur_basin->batch_size = CB_SIZE;
	cur_basin->List = (uint8*)calloc(CB_SIZE, sizeof(uint8));
	if (cur_basin->List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	cur_basin->alloc_length = CB_SIZE;
	cur_basin->List[0] = 0; // 第一位存储0，保证流域不被合并到数据范围之外
	cur_basin->length = 1;


	for (uint8 i = 0; i < sink_num; i++) {

		// 尚未被合并
		if (merge_flag[i] == 0) {
			// 加入到当前待处理流域列表中
			u8_List_append(cur_basin, min_sink + i);
			// 去除流域内部的局部最高点
			temp = _remove_inner_peak_u8(&rim_cell[i], basin, cur_basin, offset);

			// 错误情况：没有流域边界像元
			if (temp->length == 0) {
				// 给予该流域一个错误编号
				merge_flag[i] = wrong_tag++;
				// 重设辅助数据，并处理下一个流域
				cur_basin->length = 1;
				free(temp->List);
				free(temp);
				continue;
			}
			// 寻找合并到的下一个流域
			next_basin = _find_next_basin_u8(temp, elev, basin, cur_basin, offset);

			// 如果流域没有合并的外流区
			while (next_basin >= min_sink) {

				// 如果合并到一个没有处理过的内流区，继续合并
				if (merge_flag[next_basin - min_sink] == 0) {
					u8_List_append(cur_basin, next_basin);
					// 重新寻找流域边界和要合并到的流域
					temp = _eL_merge_u8(temp, &rim_cell[next_basin - min_sink], basin, cur_basin, offset);
					next_basin = _find_next_basin_u8(temp, elev, basin, cur_basin, offset);
				}
				// 如果合并到已经处理过的内流区，停止合并
				else {
					break;
				}
			}

			// 没有边界像元的错误情况
			if (next_basin == 0) {
				for (uint q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->List[q] - min_sink] = wrong_tag;
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
				for (uint q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->List[q] - min_sink] = next_basin;
				}

			}
			cur_basin->length = 1;
			free(temp->List);
			free(temp);
		}
	}

	free(cur_basin->List);
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
u64_List* _remove_inner_peak_u8(u64_List* src, unsigned char* basin, u8_List* cur_color, const int offset[]) {


	register uint64 idx = 0;
	u64_List* res = (u64_List*)malloc(sizeof(u64_List));
	if (res == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->List = (uint64*)calloc(src->length, sizeof(uint64));
	if (res->List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->batch_size = src->batch_size;
	res->alloc_length = src->length;

	for (uint i = 0; i < src->length; i++) {
		for (int j = 0; j < 8; j++) {
			idx = src->List[i] + offset[j];
			if (!check_in_u8_List(basin[idx], cur_color)) {
				res->List[res->length++] = src->List[i];
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
u64_List* _eL_merge_u8(u64_List* __restrict src, u64_List* __restrict ins, unsigned char* basin, u8_List* cur_basin, const int offset[]) {

	register uint64 idx = 0;
	uint64 all_length = src->length + ins->length;

	u64_List* res = (u64_List*)malloc(sizeof(u64_List));
	if (res == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->batch_size = src->batch_size;
	res->List = (uint64*)calloc(all_length, sizeof(uint64));
	if (res->List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	res->alloc_length = all_length;

	for (uint i = 0; i < src->length; i++) {
		for (int j = 0; j < 8; j++) {
			idx = src->List[i] + offset[j];
			if (!check_in_u8_List(basin[idx], cur_basin)) {
				res->List[res->length++] = src->List[i];
				break;
			}
		}
	}

	for (uint i = 0; i < ins->length; i++) {
		for (int j = 0; j < 8; j++) {
			idx = ins->List[i] + offset[j];
			if (!check_in_u8_List(basin[idx], cur_basin)) {
				res->List[res->length++] = ins->List[i];
				break;
			}
		}
	}

	free(src->List);
	free(src);
	src = NULL;

	return res;
}


unsigned char _find_next_basin_u8(u64_List* edge_list, float* elev, unsigned char* basin, u8_List* cur_basin, const int offset[]) {

	// 初始化参数
	uint8 next_basin = 0;
	float min_elev = 9999;
	float max_elev_diff = -9999, temp_elev_diff = 0;
	uint64 min_idx = 0, temp_idx = 0;

	if (edge_list->length > 0) {
		// 先找到边界上的最低点
		for (uint i = 0; i < edge_list->length;i++) {
			if (elev[edge_list->List[i]] < min_elev) {
				min_idx = edge_list->List[i];
				min_elev = elev[min_idx];
			}
		}
		// 再找高差最大的方向
		for (int i = 0; i < 8; i++) {
			temp_idx = min_idx + offset[i];
			temp_elev_diff = elev[min_idx] - elev[temp_idx];
			if ((temp_elev_diff > max_elev_diff) &&
				!(check_in_u8_List(basin[temp_idx], cur_basin))) {
				next_basin = basin[temp_idx];
				max_elev_diff = temp_elev_diff;
			}
		}
	}
	// 在没有边界像元的情况下返回0
	// 正常情况返回要合并入的流域的编号
	return next_basin;
}