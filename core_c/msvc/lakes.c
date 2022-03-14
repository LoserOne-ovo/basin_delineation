#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "type_aka.h"
#include "list.h"
#include "get_reverse_fdir.h"
#include "paint_upper.h"
#include "lakes.h"



/********************************
 *          湖泊河网            *
 ********************************/

 // 修正湖泊河网
int _correct_lake_network_int32(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols) {

	uint64 idx = 0;
	uint64 upper_idx = 0, down_idx = 0;
	int lake_value = 0;

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };


	// 修正河网
	for (int i = 0; i < rows; i++) {
		for (int j = 0; j < cols; j++) {

			// 如果该像元是河流像元（不属于湖泊）
			if (lake[idx] == 0 && upa[idx] > ths) {

				// 下游像元索引
				upper_idx = idx;
				down_idx = _get_down_idx64(dir[idx], idx, cols);
				lake_value = lake[down_idx];

				// 如果下游像元存在且是一个湖泊，更新湖泊范围（有可能保持不变）
				if (down_idx != 0 && lake_value > 0) {
					_update_lake(upper_idx, down_idx, lake_value, lake, re_dir, upa, ths, cols, div, offset);
				}
			}
			idx++;
		}
	}

	return 1;
}


//  修正湖泊河网，一次一个像元（递归）
int _update_lake(unsigned long long upper_idx, unsigned long long down_idx, int lake_value, int* lake,
	unsigned char* re_dir, float* upa, float ths, int cols, const unsigned char div[], const int offset[]) {

	uint64 upper_i = 0, upper_j = 0, down_i = 0, down_j = 0;
	int flag = 0;
	uint8 reverse_fdir = 0;

	// 判断下游湖泊邻近像元是否为湖泊
	down_i = down_idx / cols;
	down_j = down_idx % cols;
	upper_i = upper_idx / cols;
	upper_j = upper_idx % cols;

	// 如果上游河道像元与下游湖泊像元水平共线
	if (upper_i == down_i) {
		// 判断上游河道像元的上下两侧是否为湖泊像元
		if (lake[upper_idx - cols] == lake_value || lake[upper_idx + cols] == lake_value) {
			lake[upper_idx] = lake_value;
			flag = 1;
		}
	}
	// 如果上游河道像元与下游湖泊像元竖直共线
	else if (upper_j == down_j) {
		// 判断上游河道像元的左右两侧是否为湖泊像元
		if (lake[upper_idx - 1] == lake_value || lake[upper_idx + 1] == lake_value) {
			lake[upper_idx] = lake_value;
			flag = 1;
		}
	}
	// 如果上游河道像元与下游湖泊像元45度共线
	else {
		// 判断上游河道像元和下游湖泊像元的公共邻接像元是否为湖泊像元
		if (lake[upper_i * cols + down_j] == lake_value || lake[down_i * cols + upper_j] == lake_value)
		{
			lake[upper_idx] = lake_value;
			flag = 1;
		}
	}

	// 如果更新了湖泊的范围，那么以更新的像元为下游湖泊像元，遍历上游像元，再次更新湖泊范围，形成递归
	if (flag == 1) {

		down_idx = upper_idx;
		reverse_fdir = re_dir[upper_idx];
		for (int p = 0; p < 8; p++) {
			if (reverse_fdir >= div[p]) {
				upper_idx = down_idx + offset[p];
				if (lake[upper_idx] == 0 && upa[upper_idx] > ths) {
					_update_lake(upper_idx, down_idx, lake_value, lake, re_dir, upa, ths, cols, div, offset);
				}
				reverse_fdir -= div[p];
			}
		}
	}

	return 1;
}



// 修正湖泊河网， 当河流反复穿插湖泊，并且河流长度小于阈值，则将这段河流以及河流与湖泊之间所夹的坡面合并到湖泊中
int _correct_lake_network_2_int32(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols) {


	/********************
	 *  常规参数初始化  *
	 ********************/
	
	uint64 idx = 0;
	uint64 upper_idx = 0, down_idx = 0;
	uint64 total_num = rows * (uint64)cols;
	int lake_value = 0;
	int next_lake_value = 0;

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	
	// 开辟一个辅助标记图层，用于种子填充
	int* fill_layer = (int*)malloc(total_num * sizeof(int));
	if (fill_layer == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// 遍历图层，寻找需要修正的部分
	for (idx = 0; idx < total_num; idx++) {

		// 找到湖泊像元，它的下游在湖泊外，且是河流
		lake_value = lake[idx];
		if (lake_value > 0) {

			down_idx = _get_down_idx64(dir[idx], idx, cols);
			if (upa[down_idx] > ths) {
				next_lake_value = _find_next_water_body_int32(down_idx, lake, dir, cols);

				// 如果下游湖泊仍然是自己，则修正这条河道
				if (next_lake_value == lake_value) {
					// 先复制图层
					_copy_layer_int32(lake, fill_layer, total_num);
					// 再进行修正
					_update_lake_bound_int32(idx, lake, fill_layer, dir, cols, lake_value);
				}

			}
		}
	}
	// 释放资源
	free(fill_layer);
	fill_layer = NULL;

	// 使用第一种方法，重新修正河网
	_correct_lake_network_int32(lake, dir, re_dir, upa, ths, rows, cols);

	return 1;
}



int _copy_layer_int32(int* src, int* dst, unsigned long long total_num) {

	for (uint64 idx = 0; idx < total_num; idx++) {
		dst[idx] = src[idx];
	}
	return 1;
}


// 对于湖泊和河道不完全匹配的部分进行处理，如河流从湖泊中流出后又重新注入该湖泊。
// 这种情况会导致湖泊坡面中出现一些空洞。
// 为了避免这种情况，把河道与湖泊所夹的部分标记为湖泊。
int _update_lake_bound_int32(unsigned long long idx, int* water, int* new_layer, unsigned char* dir, int cols, int value) {

	/********************
	 *   常规参数声明   *
	 ********************/

	int down_water_id = 0;
	uint64 down_idx = 0, local_idx = 0, temp_idx = 0;
	uint8 upper_dir = 0, local_dir = 0, temp_dir = 0;

	int left_flag = 1, right_flag = 1;
	uint64 left_idx = 0, right_idx = 0;
	int left_count = 0, right_count = 0;


	/******************
	 *   参数初始化   *
	 ******************/

	down_water_id = 0;
	down_idx = _get_down_idx64(dir[idx], idx, cols);
	local_dir = dir[idx];


	/************************************
	 *   在河道的左右两侧各找一个像元   *
	 ************************************/

	while (down_water_id != value) {

		upper_dir = local_dir;
		local_idx = down_idx;
		new_layer[local_idx] = value;
		local_dir = dir[local_idx];
		down_idx = _get_down_idx64(local_dir, local_idx, cols);
		down_water_id = water[down_idx];

		if (left_flag) {

			temp_dir = _get_next_dir_clockwise(upper_dir);
			while (temp_dir != local_dir) {
				temp_idx = _get_down_idx64(temp_dir, local_idx, cols);
				if (new_layer[temp_idx] == 0) {
					left_idx = temp_idx;
					left_flag = 0;
					break;
				}
				temp_dir = _get_next_dir_clockwise(temp_dir);
			}
		}

		if (right_flag) {

			temp_dir = _get_next_dir_clockwise(local_dir);
			while (temp_dir != upper_dir) {
				temp_idx = _get_down_idx64(temp_dir, local_idx, cols);
				if (new_layer[temp_idx] == 0) {
					right_idx = temp_idx;
					right_flag = 0;
					break;
				}
				temp_dir = _get_next_dir_clockwise(temp_dir);
			}
		}
	}


	/************************
	 *   尝试修改湖泊范围   *
	 ************************/

	 // 如果河道左右两侧有一侧没有找到坡面，说明河道是贴着湖泊的
	 // 直接把河道赋成湖泊
	if (left_flag || right_flag) {

		down_idx = _get_down_idx64(dir[idx], idx, cols);
		down_water_id = 0;

		while (down_water_id != value) {
			water[down_idx] = value;
			down_idx = _get_down_idx64(dir[down_idx], down_idx, cols);
			down_water_id = water[down_idx];
		}
	}

	// 如果两侧都找到了坡面，判断哪一个坡面是加载河道和湖泊中间
	// 使用种子填充算法，分别填充河道两侧，判断哪一侧填充的数量少
	else {

		uint64 overflow_num = 1000;
		int offset_4[4] = { -1, 1, -cols, cols };
		int i = 0;
		uint64 offset_idx = 0;

		u64_List seed = { 0,0,overflow_num, NULL };
		seed.List = (uint64*)calloc(seed.alloc_length, sizeof(unsigned long long));
		if (seed.List == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}

		// 左侧
		seed.length = 0;
		seed.List[seed.length++] = left_idx;
		while (seed.length > 0 && left_count <= overflow_num) {
			temp_idx = seed.List[--seed.length];
			new_layer[temp_idx] = value;
			left_count++;

			for (i = 0; i < 4; i++) {
				offset_idx = temp_idx + offset_4[i];
				if (new_layer[offset_idx] == 0) {
					u64_List_append(&seed, offset_idx);
				}
			}
		}

		// 右侧
		seed.length = 0;
		seed.List[seed.length++] = right_idx;
		while (seed.length > 0 && right_count < overflow_num) {
			temp_idx = seed.List[--seed.length];
			new_layer[temp_idx] = value;
			right_count++;

			for (i = 0; i < 4; i++) {
				offset_idx = temp_idx + offset_4[i];
				if (new_layer[offset_idx] == 0) {
					u64_List_append(&seed, offset_idx);
				}
			}
		}

		// 对原图层进行种子填充
		if (left_count < overflow_num || right_count < overflow_num) {

			/**********************
			 *   先改变河道的值   *
			 **********************/

			down_idx = _get_down_idx64(dir[idx], idx, cols);
			down_water_id = 0;

			while (down_water_id != value) {
				water[down_idx] = value;
				down_idx = _get_down_idx64(dir[down_idx], down_idx, cols);
				down_water_id = water[down_idx];
			}

			/**************************
			 *   再改变所夹坡面的值   *
			 **************************/

			temp_idx = left_count <= right_count ? left_idx : right_idx;
			seed.length = 0;
			seed.List[seed.length++] = temp_idx;
			while (seed.length > 0 && left_count <= overflow_num) {
				temp_idx = seed.List[--seed.length];
				water[temp_idx] = value;

				for (i = 0; i < 4; i++) {
					offset_idx = temp_idx + offset_4[i];
					if (new_layer[offset_idx] == 0) {
						u64_List_append(&seed, offset_idx);
					}
				}
			}
		}
		else {
			; // 如果两侧坡面像元数量都大于阈值，直接不管
		}

		// 释放内存
		free(seed.List);
		seed.List = NULL;
		seed.length = 0;
		seed.alloc_length = 0;
	}

	return 1;
}





/********************************
 *          湖泊坡面            *
 ********************************/


// 追踪湖泊坡面
int _paint_up_lake_hillslope_int32(int* lake, int max_lake_id, unsigned char* re_dir, float* upa, float ths, int rows, int cols) {

	uint64 idx = 0, upper_idx = 0;
	uint64 total_num = rows * (uint64)cols;
	
	uint8 reverse_fdir = 0;

	int lake_value = 0; 
	int lake_hs_id = 0; // 湖泊坡面id

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };


	// 栈相对于整幅影像大小的比率
	double frac = 0.001;


	// 初始化绘制栈
	uint64 batch_size = ((uint64)(rows * (uint64)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}

	u64_List stack = { 0,0,batch_size,NULL };
	stack.List = (uint64*)calloc(batch_size, sizeof(unsigned long long));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = batch_size;

	for (idx = 0; idx < total_num; idx++) {

		lake_value = lake[idx];
		// 判断是否是湖泊像元
		if (lake_value > 0 && lake_value <= max_lake_id) {
			
			reverse_fdir = re_dir[idx];

			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					
					upper_idx = idx + offset[p];
					// 如果上游是坡面像元，则开始向上追踪坡面
					if (lake[upper_idx] == 0 && upa[upper_idx] < ths) {
						lake_hs_id = lake_value + max_lake_id;
						_paint_upper_unpainted_int32(re_dir, upper_idx, &stack, lake_hs_id, lake, offset, div);
					}
					reverse_fdir -= div[p];
				}
			}
		}
	}


	free(stack.List);
	stack.List = NULL;
	stack.length = 0;
	stack.alloc_length = 0;
	stack.batch_size = 0;

	return 1;
}



// 追踪湖泊坡面，并将连接同一个湖泊的河段也标记为坡面（如果没有其他河流）
int _paint_up_lake_hillslope_2_int32(int* lake, int max_lake_id, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols) {

	uint64 idx = 0, upper_idx = 0, down_idx = 0;
	uint64 total_num = rows * (uint64)cols;

	uint8 reverse_fdir = 0;

	int lake_value = 0;
	int lake_hs_id = 0; // 湖泊坡面id
	int next_water_id = 0;

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// 栈相对于整幅影像大小的比率
	double frac = 0.001;

	// 初始化绘制栈
	uint64 batch_size = ((uint64)(rows * (uint64)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}

	u64_List stack = { 0,0,batch_size,NULL };
	stack.List = (uint64*)calloc(batch_size, sizeof(unsigned long long));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = batch_size;

	
	/*********************
     *   绘制湖泊坡面    *
     *********************/

	for (idx = 0; idx < total_num; idx++) {

		lake_value = lake[idx];
		
		// 如果既不是河道也不是湖泊
		if (lake_value == 0 && upa[idx] < ths) {
			// 计算下游
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			// 如果是湖泊注入点
			if (lake[down_idx] > 0 && lake[down_idx] <= max_lake_id) {
				lake_hs_id = lake[down_idx] + max_lake_id;
				_paint_upper_unpainted_int32(re_dir, idx, &stack, lake_hs_id, lake, offset, div);
			}
		}
		// 如果是湖泊
		else if (lake_value > 0 && lake_value <= max_lake_id) {
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			// 如果是流出点
			if (down_idx != 0 && lake[down_idx] == 0) {
				// 找到下游水体，判断是否流入自身或自身的坡面
				next_water_id = _find_next_water_body_int32(down_idx, lake, dir, cols);
				// 如果流入自身或自身的坡面，这段河道和这段河道的坡面加入到湖泊的坡面
				if (next_water_id == lake_value || next_water_id == (lake_value + max_lake_id)) {
					lake_hs_id = lake_value + max_lake_id;
					while (lake[down_idx] == 0) {
						lake[down_idx] = lake_hs_id;
						reverse_fdir = re_dir[down_idx];

						// 找未绘制的非河道像元绘制
						for (int p = 0; p < 8; p++) {
							if (reverse_fdir >= div[p]) {
								upper_idx = down_idx + offset[p];
								if (lake[upper_idx] == 0 && upa[upper_idx] < ths) {
									_paint_upper_unpainted_int32(re_dir, upper_idx, &stack, lake_hs_id, lake, offset, div);
								}
								reverse_fdir -= div[p];
							}
						}
						down_idx = _get_down_idx64(dir[down_idx], down_idx, cols);
					}	
				}
			}
		}
		// 如果是坡面
		else {
			;
		}

	}


	free(stack.List);
	stack.List = NULL;
	stack.length = 0;
	stack.alloc_length = 0;
	stack.batch_size = 0;

	return 1;
}





/********************************
 *          湖泊流域            *
 ********************************/


// 追踪湖泊本地流域
int _paint_lake_local_catchment_int32(int* lake, int lake_num, unsigned char* re_dir, int rows, int cols) {

	uint64 idx = 0, upper_idx = 0, temp_idx = 0;
	uint64 total_num = rows * (uint64)cols;

	uint8 reverse_fdir = 0, sub_reverse_fdir = 0;

	int lake_value = 0;

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };


	// 栈相对于整幅影像大小的比率
	double frac = 0.001;


	// 初始化绘制栈
	uint64 batch_size = ((uint64)(rows * (uint64)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}

	u64_List stack = { 0,0,batch_size,NULL };
	stack.List = (uint64*)calloc(batch_size, sizeof(unsigned long long));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = batch_size;


	for (idx = 0; idx < total_num; idx++) {

		lake_value = lake[idx];
		// 如果该像元是湖泊
		if (lake_value > 0 && lake_value <= lake_num) {

			reverse_fdir = re_dir[idx];

			// 找到非湖泊的上游
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					upper_idx = idx + offset[p];

					// 如果不是湖泊像元，则开始向上追踪坡面，直到遇到其他湖泊
					if (lake[upper_idx] == 0) {
						
						stack.List[0] = upper_idx;
						stack.length = 1;

						while (stack.length > 0) {

							temp_idx = stack.List[--stack.length];
							lake[temp_idx] = lake_value;

							sub_reverse_fdir = re_dir[temp_idx];
							for (int p = 0; p < 8; p++) {
								if (sub_reverse_fdir >= div[p]) {
									sub_reverse_fdir -= div[p];
									upper_idx = temp_idx + offset[p];
									if (lake[upper_idx] == 0) {
										u64_List_append(&stack, upper_idx);
									}
								}
							}
						}
					}
					reverse_fdir -= div[p];
				}
			}
		}
	}


	free(stack.List);
	stack.List = NULL;
	stack.length = 0;
	stack.alloc_length = 0;
	stack.batch_size = 0;

	return 1;
}


// 追踪湖泊上游流域
int _paint_lake_upper_catchment_int32(int* lake, int lake_id, int* board, unsigned char* re_dir, int rows, int cols) {


	uint64 idx = 0;
	uint64 total_num = rows * (uint64)cols;
	uint64 upper_idx = 0;
	uint8 reverse_fdir = 0;

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// 栈相对于整幅影像大小的比率
	double frac = 0.001;
	uint64 batch_size = ((uint64)(rows * (uint64)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}
	// 初始化绘制栈
	u64_List stack = { 0,0,batch_size,NULL };
	stack.List = (uint64*)calloc(batch_size, sizeof(unsigned long long));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = batch_size;

	for (idx = 0; idx < total_num; idx++) {

		if (lake[idx] == lake_id) {
			board[idx] = lake_id;
			reverse_fdir = re_dir[idx];
			// 找到非湖泊的上游
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					upper_idx = idx + offset[p];
					// 如果上游不是该湖泊的像元
					if (lake[upper_idx] != lake_id) {
						_paint_upper_unpainted_int32(re_dir, upper_idx, &stack, lake_id, board, offset, div);
					}
					reverse_fdir -= div[p];
				}
			}
		}
	}


	free(stack.List);
	stack.List = NULL;
	stack.length = 0;
	stack.alloc_length = 0;
	stack.batch_size = 0;

	return 1;
}




/********************************
 *          湖泊拓扑            *
 ********************************/

// 建立湖泊之间的上下游关系
int* _topology_between_lakes(int* water, int lake_num, int* tag_array, unsigned char* dir, int rows, int cols) {

	uint64 idx = 0;
	uint64 total_num = rows * (uint64)cols;
	int default_down_lake_num = 10;

	uint64 down_idx = 0;
	int water_id = 0;
	int next_down_id = 0;
	int down_water_id = 0;

	
	// 分配空间
	i32_List* down_lake_List = (i32_List*)malloc(lake_num * sizeof(i32_List));
	if (down_lake_List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int i = 0; i < lake_num; i++) {
		down_lake_List[i].length = 0;
		down_lake_List[i].List = (int*)calloc(default_down_lake_num, sizeof(int));
		if (down_lake_List[i].List == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}
		down_lake_List[i].batch_size = default_down_lake_num;
		down_lake_List[i].alloc_length = default_down_lake_num;
	}

	for (idx = 0; idx < total_num; idx++) {

		water_id = water[idx];
		if (water_id > 0) {

			// 判断湖泊内的内流区终点
			if (dir[idx] == 255) {
				if (!check_in_i32_List(water_id, &down_lake_List[water_id - 1])) {
					i32_List_append(&down_lake_List[water_id - 1], water_id);
				}
				continue;
			}

			//判断是否是湖泊出水口
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			next_down_id = water[down_idx];
			
			// 下游还是这个湖泊
			if (next_down_id == water_id) {
				continue;
			}
			// 下游不是湖泊
			else if (next_down_id == 0) {				
				// 寻找下游湖泊
				down_water_id = _find_next_water_body_int32(down_idx, water, dir, cols);
				
				// 没有下游湖泊或下游仍然是这个湖泊
				if (down_water_id <= 0 || down_water_id == water_id) {
					continue;
				}
				// 下游是其他湖泊
				else {
					// 检查是否已经记录了这个湖泊
					if (!check_in_i32_List(down_water_id, &down_lake_List[water_id - 1])) {
						i32_List_append(&down_lake_List[water_id - 1], down_water_id);
					}
				}
			}
			// 下游是其他湖泊
			else if (next_down_id > 0) {
				next_down_id *= -1;
				if (!check_in_i32_List(down_water_id, &down_lake_List[water_id - 1])) {
					i32_List_append(&down_lake_List[water_id - 1], down_water_id);
				}
			}
			// 下游在流域外
			else {
				continue;
			}
		}

		
		/****************************************
		 *  未来可以通过出水口的上游湖泊面积，  *
		 *  判断该出水口是否是湖泊真正的出水口  *
		 ****************************************/
	}


	// 最后把下游湖泊的ID转成一维数组返回
	int total_down = 0;
	for (int i = 0; i < lake_num; i++) {
		total_down += down_lake_List[i].length;
		tag_array[i] = total_down;
	}
	
	int insert_probe = 0;
	int* result = (int*)calloc(total_down, sizeof(int));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int i = 0; i < lake_num; i++) {
		for (int j = 0; j < down_lake_List[i].length; j++) {
			result[insert_probe++] = down_lake_List[i].List[j];
		}
	}

	// 释放内存
	for (int i = 0; i < lake_num; i++) {
		free(down_lake_List[i].List);
		down_lake_List[i].List = NULL;
	}
	free(down_lake_List);
	down_lake_List = NULL;

	return result;
}


// 找到下游的水体 
int _find_next_water_body_int32(unsigned long long idx, int* water, unsigned char* dir, int cols) {

	uint64 down_idx = idx;
	int down_water_id = 0;
	uint8 temp_dir = 0;

	do {
		// 计算下游像元位置
		temp_dir = dir[down_idx];
		down_idx = _get_down_idx64(temp_dir, down_idx, cols);
		
		// 如果找不到下游了
		if (down_idx == 0) {
			if (temp_dir == 255) {
				return -1;
			}
			else {
				return 0;
			}
		}
		down_water_id = water[down_idx];

	} while (down_water_id <= 0);

	return down_water_id;
}


// 标记D8流向中所有潜在的湖泊出水口
int _mark_lake_outlet_int32(int* lake, int min_lake_id, int max_lake_id, unsigned char* dir, int rows, int cols) {

	uint64 idx = 0, down_idx = 0;
	uint64 total_num = rows * (uint64)cols;
	uint8 temp_dir = 0;
	int lake_id = 0;

	for (idx = 0; idx < total_num; idx++) {

		lake_id = lake[idx];
		// 如果是湖泊像元，判断是否为湖泊出口
		if (lake_id >= min_lake_id && lake_id <= max_lake_id) {

			temp_dir = dir[idx];
			if (temp_dir == 0 || temp_dir == 247) {
				lake[idx] *= 3;
			}
			else if (temp_dir == 255) {
				lake[idx] *= 2;
			}
			else {

				down_idx = _get_down_idx64(temp_dir, idx, cols);
				if (lake[down_idx] != lake_id && lake[down_idx] != (2 * lake_id)) {
					lake[idx] *= 2;
				}
			}
		}
	}

	return 1;
}


// 建立湖泊之间的流路
unsigned long long* _route_between_lake(int* lake, int lake_num, unsigned char* dir, float* upa, int rows, int cols, 
	int* return_num, unsigned long long* return_length) {


	uint64 idx = 0;
	uint64 total_num = rows * (uint64)cols;
	uint64 down_idx = 0;
	int lake_id = 0;
	int next_down_id = 0;
	int down_lake_id = 0;


	lake_pour* lake_down_list = (lake_pour*)malloc(lake_num * sizeof(lake_pour));
	if (lake_down_list == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int i = 0; i < lake_num; i++) {
		lake_down_list[i].num = 0;
		lake_down_list[i].List = NULL;
	}

	// 找个每个湖泊的到下游湖泊的出水口，一个下游湖泊只保留一个出水口，取汇流累积量最大的
	// 允许一个湖泊有多个下游湖泊
	for (idx = 0; idx < total_num; idx++) {
		
		lake_id = lake[idx];
		// 如果是湖泊
		if (lake_id > 0) {
			// 如果是湖泊内部的内流区终点
			if (dir[idx] == 255) {
				// 在湖泊下游列表中插入自己
				_insert_lake_down_water(&lake_down_list[lake_id - 1], lake_id, lake_id, idx, upa);
				continue;
			}

			//判断是否是湖泊出水口
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			next_down_id = lake[down_idx];
			// 下游还是这个湖泊
			if (next_down_id == lake_id) {
				continue;
			}
			// 下游不是湖泊
			else if (next_down_id == 0) {
				// 寻找下游湖泊
				down_lake_id = _find_next_water_body_int32(down_idx, lake, dir, cols);
				// 如果下游位于其他湖泊的本地流域
				if (down_lake_id > 0 && down_lake_id != lake_id) {
					_insert_lake_down_water(&lake_down_list[lake_id - 1], lake_id, down_lake_id, idx, upa);
				}
				// 如果下游不流向某个湖泊，并位于某个内流区内
				else if (down_lake_id == -1) {
					_insert_lake_down_water(&lake_down_list[lake_id - 1], lake_id, lake_id, idx, upa);
				}
				else {
					continue;
				}
			}
			// 下游是其他湖泊
			else if (next_down_id > 0) {
				_insert_lake_down_water(&lake_down_list[lake_id - 1], lake_id, next_down_id, idx, upa);
				continue;
			}
			// 下游在流域外
			else {
				continue;
			}
		}
	}


	// 统计湖泊之间的流路的数量
	int route_num = 0;
	for (int i = 0; i < lake_num; i++) {
		if (lake_down_list[i].num > 0) {
			for (int j = 0; j < lake_down_list[i].num; j++) {
				if (lake_down_list[i].List[j].upper_water != lake_down_list[i].List[j].down_water) {
					route_num += 1;
				}
			}
		}
	}

	// 初始化流路
	lake_route* routeList = (lake_route*)malloc(route_num * sizeof(lake_route));
	if (routeList == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int i = 0; i < route_num; i++) {
		routeList[i].upper_water = 0;
		routeList[i].down_water = 0;
		routeList[i].route.length = 0;
		routeList[i].route.batch_size = DEFAULT_PATH_LENGTH;
		routeList[i].route.List = (unsigned long long*)calloc(DEFAULT_PATH_LENGTH, sizeof(unsigned long long));
		if (routeList[i].route.List == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}
		routeList[i].route.alloc_length = DEFAULT_PATH_LENGTH;
	}

	// 计算流路
	int route_id = 0;
	int upper_id = 0;
	int down_id = 0;
	uint64 outlet_idx = 0;

	
	// 循环提取流路
	for (int i = 0; i < lake_num; i++) {
		if (lake_down_list[i].num > 0) {
			for (int j = 0; j < lake_down_list[i].num; j++) {
				upper_id = lake_down_list[i].List[j].upper_water;
				down_id = lake_down_list[i].List[j].down_water;
				outlet_idx = lake_down_list[i].List[j].outlet_idx;	
				// 提取流路
				if (upper_id != down_id) {
					routeList[route_id].upper_water = upper_id;
					routeList[route_id].down_water = down_id;
					_extract_route(&routeList[route_id].route, down_id, outlet_idx, lake, dir, cols);
					route_id++;
				}
			}
		}
	}
	

	// 以一维数组的形式返回给Python
	// 统计数组长度
	uint64 result_length = 0;
	for (int i = 0; i < route_num; i++) {
		result_length += 3 + routeList[i].route.length;
	}
	// 分配内存
	unsigned long long* result = (uint64*)calloc(result_length, sizeof(unsigned long long));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	*return_num = route_num;
	*return_length = result_length;
	uint64 offset = 0;
	// 拷贝数组
	for (int i = 0; i < route_num; i++) {
		result[offset + 0] = (uint64)routeList[i].upper_water;
		result[offset + 1] = (uint64)routeList[i].down_water;
		result[offset + 2] = routeList[i].route.length;
		offset += 3;
		for (uint64 m = 0; m < routeList[i].route.length; m++) {
			result[offset + m] = routeList[i].route.List[m];
		}
		offset += routeList[i].route.length;
	}
	

	// 释放内存
	for (int i = 0; i < lake_num; i++) {
		if (lake_down_list[i].num > 0) {
			free(lake_down_list[i].List);
		}
	}
	free(lake_down_list);
	lake_down_list = NULL;
	
	for (int i = 0; i < route_num; i++) {
		free(routeList[i].route.List);
	}
	free(routeList);
	routeList = NULL;


	return result;
}


int _insert_lake_down_water(lake_pour* src, int src_id, int down_id, unsigned long long outlet_idx, float* upa){

	// 判断是否已经存在该下游
	int exist_flag = _check_lake_down_existed(src, down_id);
	// 如果不存在，直接插入
	if (exist_flag < 0){
		water_pour* newList = (water_pour*)realloc(src->List, (src->num + DEFAULT_POUR_NUM) * sizeof(water_pour));
		if (newList == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}
		src->List = newList;
		src->List[src->num].upper_water = src_id;
		src->List[src->num].down_water = down_id;
		src->List[src->num].outlet_idx = outlet_idx;
		src->num++;
	}
	// 如果存在，取汇流累积量最大的出水口
	else
	{
		if (upa[outlet_idx] > upa[src->List[exist_flag].outlet_idx]) {
			src->List[exist_flag].outlet_idx = outlet_idx;
		}
	}

	return 1;
}

int _check_lake_down_existed(lake_pour* src, int down_id) {

	for (int i = 0; i < src->num; i++) {
		if (src->List[i].down_water == down_id) {
			return i;
		}
	}
	return -1;
}


int _extract_route(u64_List* src, int down_water, unsigned long long outlet_idx, int* lake, unsigned char* dir, int cols) {


	uint8 upper_dir = 255;
	uint8 temp_dir = 0;
	uint64 temp_idx = outlet_idx;
	int next_water_id = 0;

	do {
		temp_dir = dir[temp_idx];
		// 简化流路
		if (temp_dir != upper_dir) {
			u64_List_append(src, temp_idx);
			upper_dir = temp_dir;
		}
		temp_idx = _get_down_idx64(temp_dir, temp_idx, cols);
		next_water_id = lake[temp_idx];
	} while(next_water_id != down_water);

	u64_List_append(src, temp_idx);

	return 1;
}