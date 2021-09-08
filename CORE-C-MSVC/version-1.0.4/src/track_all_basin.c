#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "get_reverse_fdir.h"
#include "list.h"



unsigned char* _track_all_basins(unsigned char* dir, int rows, int cols) {

	uint64 cols64 = (uint64)cols;
	uint64 total_num = cols64 * rows;
	double frac = 0.01;
	uint64 QUENE_SIZE = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (QUENE_SIZE > 100000000) {
		QUENE_SIZE = 100000000;
	}



	uint8* re_dir = _get_re_dir(dir, rows, cols);
	uint8* basin = (uint8*)calloc(total_num, sizeof(unsigned char));
	if (basin == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}


	uint64 sb_list_size = 10000;
	u64_List sink_bottom = { 0,0,sb_list_size,NULL };
	sink_bottom.List = (uint64*)calloc(sb_list_size, sizeof(unsigned long long));
	if (sink_bottom.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	sink_bottom.alloc_length = sb_list_size;


	uint8 reverse_fdir = 0;
	uint8 color = 1;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_List stack = { 0,0,QUENE_SIZE,NULL };
	stack.List = (uint64*)calloc(QUENE_SIZE, sizeof(unsigned long long));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = QUENE_SIZE;

	register uint64 idx = 0, temp_idx = 0;
	for (idx = 0; idx < total_num; idx++) {
		
		if (dir[idx] == 0) {

			stack.List[0] = idx;
			stack.length = 1;

			while (stack.length > 0) {
				// 出栈上色
				temp_idx = stack.List[stack.length - 1];
				stack.length--;
				basin[temp_idx] = color;
				// 上游入栈
				reverse_fdir = re_dir[temp_idx];
				for (int p = 0; p < 8; p++) {
					if (reverse_fdir >= div[p]) {
						u64_List_append(&stack, temp_idx + offset[p]);
						reverse_fdir -= div[p];
					}
				}
			}
		}
		else if (dir[idx] == 255) {
			u64_List_append(&sink_bottom, idx);
		}
		else {
			;
		}
	}

	int round_change = 0;
	int temp_flag = 0;
	int* sb_flag = (int*)calloc(sink_bottom.length, sizeof(int));
	if (sb_flag == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}



	do {

		// 一轮中新合并的内流区的数量
		round_change = 0;

		for (uint64 i = 0; i < sink_bottom.length; i++) {
			// 循环所有的内流区，判断是否已经加入到合并的流域中
			if (sb_flag[i] == 0) {
				// 是否合并的标记
				temp_flag = 0;
				stack.List[0] = sink_bottom.List[i];
				stack.length = 1;

				while (stack.length > 0) {
					temp_idx = stack.List[stack.length - 1];
					stack.length--;
					reverse_fdir = re_dir[temp_idx];

					// 只要有一个边界像元相连，就判断直接合并
					if (reverse_fdir == 0) {
						for (int p = 0; p < 8; p++) {
							if (basin[temp_idx + offset[p]] == 1) {
								sb_flag[i] = 1;
								temp_flag = 1;
								break;
							}
						}
						if (temp_flag == 1) {
							break;
						}
					}
					else {
						for (int p = 0; p < 8; p++) {
							if (reverse_fdir >= div[p]) {
								u64_List_append(&stack, temp_idx + offset[p]);
								reverse_fdir -= div[p];
							}
						}
					}
				}

				// 如果内流区与已知的流域有相连处，则将内流区合并到已知的流域中
				if (temp_flag == 1) {
					stack.List[0] = sink_bottom.List[i];
					stack.length = 1;

					while (stack.length > 0) {
						temp_idx = stack.List[stack.length - 1];
						stack.length--;
						basin[temp_idx] = color;
						reverse_fdir = re_dir[temp_idx];

						for (int p = 0; p < 8; p++) {
							if (reverse_fdir >= div[p]) {
								u64_List_append(&stack, temp_idx + offset[p]);
								reverse_fdir -= div[p];
							}
						}
					}
					round_change++;
				}
			}
		}
	} while (round_change > 0); // 如果一轮循环后没有内流区合并到已知的流域中，就结束循环


	free(stack.List);
	stack.List = NULL;
	free(sb_flag);
	sb_flag = NULL;
	free(sink_bottom.List);
	sink_bottom.List = NULL;
	free(re_dir);
	re_dir = NULL;


	return basin;
}





