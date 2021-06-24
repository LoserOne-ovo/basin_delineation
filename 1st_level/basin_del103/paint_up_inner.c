#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "paint_up_inner.h"


/// <summary>
/// 内流区处理
/// </summary>
/// <param name="ridx"></param>
/// <param name="cidx"></param>
/// <param name="cols"></param>
/// <param name="inner_num"></param>
/// <param name="outer_num"></param>
/// <param name="re_fdir"></param>
/// <param name="basin"></param>
/// <param name="dem"></param>
/// <returns></returns>
__declspec(dllexport) int paint_up_inner(unsigned int* ridx, unsigned int* cidx, int cols, 
										 unsigned int inner_num, unsigned int outer_num, 
										 unsigned char* re_fdir, unsigned short* basin, float* dem) 
{
	
	uint64 idx = 0;
	uint64 cols64 = (uint64)cols;
	
	// 存储每一个内流区的边界像元
	u64_List* rim_cell = (u64_List*)calloc(inner_num, sizeof(u64_List));
	if (rim_cell == NULL) {
		fprintf(stderr, "memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
		exit(-1);
	}
	for (uint i = 0; i < inner_num; i++) {

		rim_cell[i].List = (uint64*)calloc(L_SIZE, sizeof(uint64));
		if (rim_cell[i].List == NULL) {
			fprintf(stderr, "memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
			exit(-1);
		}
		rim_cell[i].alloc_length = L_SIZE;
		rim_cell[i].length = 0;
	}

	
	uint8 reverse_fdir = 0;
	uint16 color;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_List quene = { 0,0,NULL };

	quene.List = (uint64*)calloc(LL_SIZE, sizeof(uint64));
	if (quene.List == NULL) {
		fprintf(stderr, "Memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
		exit(-1);
	}
	quene.alloc_length = LL_SIZE;

	
	for (uint i = 0; i < inner_num; i++) {

		idx = ridx[i] * cols64 + cidx[i];
		color = 10000 + i;

		quene.List[0] = idx;
		quene.length = 1;

		while (quene.length > 0) {
			idx = quene.List[quene.length - 1];
			basin[idx] = color;
			quene.length--;
			reverse_fdir = re_fdir[idx];
			
			// 在追溯的过程中，如果一个像元没有上游，那么就认为是边界像元
			if (reverse_fdir == 0) {
				u64_List_append(&rim_cell[i], idx, L_SIZE);
			}
			else {
				for (int p = 0; p < 8; p++) {
					if (reverse_fdir >= div[p]) {
						u64_List_append(&quene, idx + offset[p], LL_SIZE);
						reverse_fdir -= div[p];
					}
				}
			}
			
		}

	}
	

	// 将内流域合并到外流区，以外流区编号记录下合并结果
	uint16* merge_flag = inner_merge(inner_num, outer_num, rim_cell, basin, dem, offset);

	for (uint i = 0;i < inner_num;i++) {
		free(rim_cell[i].List);
	}
	free(rim_cell);
	rim_cell = NULL;


	// 以新的编号重新追溯上游
	for (uint i = 0;i < inner_num; i++) {

		idx = ridx[i] * cols64 + cidx[i];
		color = merge_flag[i];
		quene.List[0] = idx;
		quene.length = 1;

		while (quene.length > 0) {
			idx = quene.List[quene.length - 1];
			basin[idx] = color;
			quene.length--;
			reverse_fdir = re_fdir[idx];

			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_List_append(&quene, idx + offset[p], LL_SIZE);
					reverse_fdir -= div[p];
				}
			}	
		}
	}

	free(quene.List);
	free(merge_flag);

	return 1;

}


/// <summary>
/// 内流区合并
/// </summary>
/// <param name="inner_num"></param>
/// <param name="outer_num"></param>
/// <param name="rim_cell"></param>
/// <param name="basin"></param>
/// <param name="elev"></param>
/// <param name="offset"></param>
/// <returns></returns>
unsigned short* inner_merge(int inner_num, int outer_num, u64_List* rim_cell, unsigned short* basin, float* elev, const int offset[])
{

	uint16* merge_flag = (uint16*)calloc(inner_num, sizeof(uint16));
	if (merge_flag == NULL) {
		fprintf(stderr, "Memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
		exit(-1);
	}
	uint16 wrong_tag = 10000;
	uint16 next_basin = 0;

	u64_List* temp;

	// 记载当前的流域编号，用于去除非边界像元
	u16_List* cur_basin = (u16_List*)malloc(sizeof(u16_List));
	if (cur_basin == NULL) {
		fprintf(stderr, "Memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
		exit(-1);
	}
	cur_basin->List = (uint16*)calloc(M_SIZE, sizeof(uint16));
	if (cur_basin->List == NULL) {
		fprintf(stderr, "Memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
		exit(-1);
	}
	cur_basin->alloc_length = M_SIZE;
	cur_basin->List[0] = 0;
	cur_basin->length = 1;


	for (int i = 0; i < inner_num; i++) {

		// 尚未被合并
		if (merge_flag[i] == 0) {

			u16_List_append(cur_basin, (uint16)(10000 + i), M_SIZE);
			temp = remove_inner_peak(&rim_cell[i], basin, cur_basin, offset);
			
			// 没有边界像元的错误情况
			if (temp->length == 0) {
				merge_flag[i] = wrong_tag++;
				
				cur_basin->length = 1;
				free(temp->List);
				free(temp);
				continue;
			}
			
			next_basin = find_next_basin(temp, elev, basin, cur_basin, offset);
			
			// 如果流域没有合并的外流区
			while (next_basin > outer_num) {
				
				// 如果合并到的是没有处理过的内流区，继续合并
				if (merge_flag[next_basin - 10000] == 0) {
					u16_List_append(cur_basin, next_basin, M_SIZE);
					temp = eL_merge(temp, &rim_cell[next_basin - 10000], basin, cur_basin, offset);
					next_basin = find_next_basin(temp, elev, basin, cur_basin, offset);
				}
				// 如果合并到已经处理过的内流区，停止合并
				else {
					break;
				}
			}

			// 没有边界像元的错误情况
			if (next_basin == 0) {
				for (uint q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->List[q] - 10000] = wrong_tag;
				}
				wrong_tag++;
			}
			// 正常情况
			else {
				
				// 合并到处理过的内流区，则合并到该内流区对应的外流区 
				if (next_basin > outer_num) {
					next_basin = merge_flag[next_basin - 10000];
				}
				// 合并
				for (uint q = 1; q < cur_basin->length; q++) {
					merge_flag[cur_basin->List[q] - 10000] = next_basin;
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
u64_List* remove_inner_peak(u64_List* src, unsigned short* basin, u16_List* cur_color, const int offset[]) {
	
	
	uint64 idx = 0;
	u64_List* res = (u64_List*)malloc(sizeof(u64_List));
	if (res == NULL) {
		fprintf(stderr, "Memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
		exit(-1);
	}
	res->List = (uint64*)calloc(src->length, sizeof(uint64));
	if (res->List == NULL) {
		fprintf(stderr, "Memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->alloc_length = src->length;


	for (uint i = 0; i < src->length; i++) {

		for (uint j = 0; j < 8; j++) {

			idx = src->List[i] + offset[j];
			if (!check_in_u16_List(basin[idx], cur_color)) {
				res->List[res->length++] = src->List[i];
				break;
			}
		}
	}

	return res;
}



/// <summary>
/// 寻找要合并的流域
/// </summary>
/// <param name="edge_list"></param>
/// <param name="elev"></param>
/// <param name="basin"></param>
/// <param name="cur_basin"></param>
/// <param name="offset"></param>
/// <returns></returns>
unsigned short find_next_basin(u64_List* edge_list, float* elev, unsigned short* basin, u16_List* cur_basin, const int offset[]) {


	uint16 next_basin = 0;
	float min_elev = 9999;
	float max_elev_diff = -9999, temp_elev_diff = 0;
	uint64 min_idx = 0, temp_idx = 0;

	
	if (edge_list->length > 0) {

		// 先找的边界上的最低点
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
	
	// 没有边界像元的情况返回0
	return next_basin;

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
u64_List* eL_merge(u64_List* src, u64_List* ins, unsigned short* basin, u16_List* cur_basin, const int offset[]){


	uint64 idx = 0;
	uint all_length = src->length + ins->length;
	
	u64_List* res = (u64_List*)malloc(sizeof(u64_List));
	if (res == NULL) {
		fprintf(stderr, "Memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
		exit(-1);
	}
	res->length = 0;
	res->List = (uint64*)calloc(all_length, sizeof(uint64));
	if (res->List == NULL) {
		fprintf(stderr, "Memory allocation failed in line %d of paint_up_inner.c \r\n", __LINE__);
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