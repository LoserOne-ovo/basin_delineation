#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "list.h"
#include "get_reverse_fdir.h"
#include "paint_up.h"
#include "river.h"



int* _dfn_stream(unsigned char* __restrict dir, float* __restrict upa, float ths, int outlet_ridx, int outlet_cidx, int rows, int cols) {


	uint64 total_num = rows * (uint64)cols;
	uint64 idx = 0, upper_idx = 0;
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };

	// 初始化结果
	int* __restrict result = (int*)calloc(total_num, sizeof(int));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// 计算逆流向
	unsigned char* re_dir = _get_re_dir(dir, rows, cols);


	/* 深度遍历为每一个河道进行赋值*/

	// 辅助变量
	uint8 reverse_fdir = 0;
	int channel_id = 10001;
	uint8 upper_channel_num = 0;
	uint64 temp_upper_List[8] = { 0 };
	
	// 预设河段的规模为100000
	int bench_channel_num = 100000;
	// 还是使用栈数据结构
	u64_List streams = { 0,0, bench_channel_num, NULL };
	streams.List = (uint64*)calloc(bench_channel_num, sizeof(unsigned long long));
	if (streams.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// 计算流域出口一维索引
	idx = (uint64)(outlet_ridx * (uint64)cols + outlet_cidx);
	streams.List[0] = idx;
	streams.length = 1;
	
	// 如果流域出口处的汇流累积量小于阈值
	if (upa[idx] <= ths) {
		fprintf(stderr, "Flow accumulation of the outlet is less than the threshold!\r\n");
	}
	// 正常计算
	else {

		// 在循环内使用break跳出循环，节省比较次数
		while (1) {

			// 给河道像元赋值
			result[idx] = channel_id;
			// 获取逆流向
			reverse_fdir = re_dir[idx];
			// 重置上游河道数量
			upper_channel_num = 0;

			// 遍历上游像元，寻找河道
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					// 计算上游像元一维索引
					reverse_fdir -= div[p];
					upper_idx = idx + offset[p];
					// 如果上游像元是一个河道，则记录该像元
					if (upa[upper_idx] > ths) {
						temp_upper_List[upper_channel_num++] = upper_idx;
					}
				}
			}

			// 如果只有一个上游河道像元，说明还处在同一个河段
			if (upper_channel_num == 1) {
				idx = temp_upper_List[0];
			}

			// 如果有多个河道像元，说明处于河道交叉处，结束当前河段，并添加新的河段
			else if (upper_channel_num > 1) {
				streams.length--;
				for (int q = 0; q < upper_channel_num; q++) {
					u64_List_append(&streams, temp_upper_List[q]);
				}
				idx = streams.List[streams.length - 1];
				channel_id++;
			}

			// 如果没有上游河道像元，说明河段结束
			else {
				streams.length--;
				if (streams.length > 0) {
					idx = streams.List[streams.length - 1];
					channel_id++;
				}
				// 如果栈中没有其他河道，则退出循环
				else {
					break;
				}
			}
		}

	}


	free(streams.List);
	streams.List = NULL;
	streams.length = 0;
	streams.batch_size = 0;
	streams.alloc_length = 0;

	free(re_dir);
	re_dir = NULL;

	return result;
}


/*
	nodata_cell = 0,
	lake_cell > 1,
	other_basin_cell = 1

*/
int _dfn_stream_overlap_lake(int* __restrict lake, unsigned char* __restrict dir, float* __restrict upa, 
	float ths, int outlet_ridx, int outlet_cidx, int rows, int cols) {


	uint64 idx = 0, upper_idx =0;
	uint64 total_num = rows * (uint64)cols;

	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };

	// 计算逆流向
	unsigned char* re_dir = _get_re_dir(dir, rows, cols);

	/* 深度遍历为每一个河道进行赋值*/

	// 辅助变量
	uint8 reverse_fdir = 0;
	int channel_id = 10000;
	uint8 upper_channel_num = 0;
	uint64 temp_upper_List[8] = { 0 };
	int channel_end_flag = 0;

	// 预设河段的规模为100000
	int bench_channel_num = 100000;
	// 还是使用栈数据结构
	u64_List streams = { 0,0, bench_channel_num, NULL };
	streams.List = (uint64*)calloc(bench_channel_num, sizeof(unsigned long long));
	if (streams.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// 计算流域出口一维索引
	idx = (uint64)(outlet_ridx * (uint64)cols + outlet_cidx);
	streams.List[0] = idx;
	streams.length = 1;

	// 如果流域出口处的汇流累积量小于阈值
	if (upa[idx] <= ths) {
		fprintf(stderr, "Flow accumulation of the outlet is less than the threshold!\r\n");
	}
	
	// 正常计算
	else {

		while (streams.length > 0) {

			idx = streams.List[--streams.length];
			channel_end_flag = 0;

			// 如果河段的起始在湖泊外
			if (lake[idx] == 1) {

				channel_id++;
				while (channel_end_flag == 0) {

					lake[idx] = channel_id;
					// 获取逆流向
					reverse_fdir = re_dir[idx];
					// 重置上游河道数量
					upper_channel_num = 0;

					// 遍历上游像元，寻找河道
					for (int p = 0; p < 8; p++) {
						if (reverse_fdir >= div[p]) {
							// 计算上游像元一维索引
							reverse_fdir -= div[p];
							upper_idx = idx + offset[p];
							// 如果上游像元是一个河道，则记录该像元
							if (upa[upper_idx] > ths) {
								temp_upper_List[upper_channel_num++] = upper_idx;
							}
						}
					}

					// 如果只有上游只有一个河段像元
					if (upper_channel_num == 1) {
						upper_idx = temp_upper_List[0];
						// 如果上游河道像元也位于湖泊外，不产生新的河段
						if (lake[upper_idx] == 1) {
							idx = upper_idx;
						}
						// 如果上游河道像元位于湖泊内，结束当前河段，产生新的河段
						else {
							u64_List_append(&streams, upper_idx);
							channel_end_flag = 1;
						}

					}
					// 如果上游有多个河道像元,则结束当前河段，添加新河段
					else if (upper_channel_num > 1) {
						for (uint8 q = 0; q < upper_channel_num; q++) {
							u64_List_append(&streams, temp_upper_List[q]);
						}
						channel_end_flag = 1;
					}
					// 如果上游没有河道像元，则结束当前河段
					else {
						channel_end_flag = 1;
					}
				} // 结束湖泊外某一条河段的追踪
			}

			// 如果河段的起始在湖泊内
			else {

				while (channel_end_flag == 0) {

					// 获取逆流向
					reverse_fdir = re_dir[idx];
					// 重置上游河道数量
					upper_channel_num = 0;

					// 遍历上游像元，寻找河道
					for (int p = 0; p < 8; p++) {
						if (reverse_fdir >= div[p]) {
							// 计算上游像元一维索引
							reverse_fdir -= div[p];
							upper_idx = idx + offset[p];
							// 如果上游像元是一个河道，则记录该像元
							if (upa[upper_idx] > ths) {
								temp_upper_List[upper_channel_num++] = upper_idx;
							}
						}
					}

					// 如果只有上游只有一个河段像元
					if (upper_channel_num == 1) {
						// 如果上游河道像元也位于湖泊内，不产生新的河段
						upper_idx = temp_upper_List[0];
						if (lake[upper_idx] > 1) {
							idx = upper_idx;
						}
						// 如果上游河道像元位于湖泊外，产生新的河段
						else {
							u64_List_append(&streams, upper_idx);
							channel_end_flag = 1;
						}

					}
					// 如果上游有多个河道像元,则结束当前河段，添加新河段
					else if (upper_channel_num > 1) {
						for (uint8 q = 0; q < upper_channel_num; q++) {
							u64_List_append(&streams, temp_upper_List[q]);
						}
						channel_end_flag = 1;
					}
					// 如果上游没有河道像元，则结束当前河段
					else {
						channel_end_flag = 1;
					}

				} // 结束湖泊内某一条河段的追踪

			}

		}

	}

	free(streams.List);
	streams.List = NULL;
	streams.length = 0;
	streams.batch_size = 0;
	streams.alloc_length = 0;

	free(re_dir);
	re_dir = NULL;

	return 1;

}



// 绘制河道的山坡单元
int _paint_river_hillslope_int32(int* __restrict stream, int min_channel_id, int max_channel_id, unsigned char* __restrict dir, unsigned char* __restrict re_dir, int rows, int cols) {


	/**************************
	 *      初始化参数        *
	 **************************/
	
	
	// 经验参数
	int bench_size = 100000;

	// 常量
	uint64 total_num = rows * (uint64)cols;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	//const uint8 fdc[8] = { 1,2,4,8,16,32,64,128 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// 辅助变量
	uint64 idx = 0, temp_idx = 0, upper_idx = 0;
	uint8 reverse_fdir = 0, temp_reverse_fdir = 0;
	uint8 cur_dir = 0;
	uint8 upper_channel_num = 0, upper_hs_num = 0;
	int hillslope_id = 0, channel_id = 0;
	uint8 cur_idx = 0;

	// 辅助列表
	uint64 temp_upper_idx_List[8] = { 0 };
	uint8 temp_upper_dir_List[8] = { 0 };
	uint8 temp_upper_stream_dir_List[8] = { 0 };
	
	// 辅助栈
	u64_List stack = { 0,0,bench_size,NULL };
	stack.List = (uint64*)calloc(bench_size, sizeof(unsigned long long));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}


	/**************************
	 *      绘制河道坡面      *
     **************************/


	uint64 count = 0;


	// 循环整幅影像
	for (idx = 0; idx < total_num; idx++) {

		channel_id = stream[idx];


		// 如果是河道像元
		if (channel_id >= min_channel_id && channel_id <= max_channel_id) {

			count++;
			/*fprintf(stderr, "%llu ", count);*/


			// 重置辅助变量
			upper_channel_num = upper_hs_num = 0;
			reverse_fdir = re_dir[idx];

			// 计算当前像元的上游河道数量和索引
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					reverse_fdir -= div[p];
					upper_idx = idx + offset[p];
					// 如果上游像元是一个河道，则记录该像元
					if (stream[upper_idx] >= min_channel_id) {
						temp_upper_stream_dir_List[upper_channel_num++] = div[p];
					}
					else {
						temp_upper_dir_List[upper_hs_num] = div[p];
						temp_upper_idx_List[upper_hs_num++] = upper_idx;
					}
				}
			}
			
			cur_dir = dir[idx];
			fprintf(stderr, "%d-%d  ", cur_dir, upper_channel_num);

			// 如果是内流区终点,暂时当做源头坡处理
			if (cur_dir == 255) {
				hillslope_id = max_channel_id + (channel_id - min_channel_id) * 3 + 1;
				for (int q = 0; q < upper_hs_num; q++) {
					_paint_upper_int32(re_dir, temp_upper_idx_List[q], &stack, hillslope_id, stream, offset, div);
				}
			}
			else {

				// 如果是入海口，找一个海洋像元，定位流向
				if (cur_dir == 0) {
					
					for (uint8 p = 0; p < 8; p++) {
						temp_idx = idx + offset[p];
						if (dir[temp_idx] == 247) {
							cur_dir = div[p];
							break;
						}
					}
				}

				/************************************
				 *    判断当前像元在河道中的位置    *
				 * **********************************/

				 /* 1.河道源头 */
				if (upper_channel_num == 0) {

					hillslope_id = max_channel_id + (channel_id - min_channel_id) * 3 + 1;
					for (int q = 0; q < upper_hs_num; q++) {
						_paint_upper_int32(re_dir, temp_upper_idx_List[q], &stack, hillslope_id, stream, offset, div);
					}
				}


				/* 2.河道中央（只有一个上游）*/
				else if (upper_channel_num == 1) {

					for (int q = 0; q < upper_hs_num; q++) {
						hillslope_id = _decide_hillslope_id(cur_dir, temp_upper_dir_List[q], temp_upper_stream_dir_List,
							upper_channel_num, channel_id, min_channel_id, max_channel_id);
						_paint_upper_int32(re_dir, temp_upper_idx_List[q], &stack, hillslope_id, stream, offset, div);
					}
				}


				/* 2.河道交叉（多个上游）*/
				else {
					cur_dir = dir[idx];
					for (int q = 0; q < upper_hs_num; q++) {
						hillslope_id = _decide_hillslope_id(cur_dir, temp_upper_dir_List[q], temp_upper_stream_dir_List,
							upper_channel_num, channel_id, min_channel_id, max_channel_id);
						_paint_upper_int32(re_dir, temp_upper_idx_List[q], &stack, hillslope_id, stream, offset, div);
					}
				}
			}
		}
	}

	// 释放资源
	free(re_dir);
	re_dir = NULL;
	free(stack.List);
	stack.List = NULL;
	stack.alloc_length = 0;
	stack.length = 0;

	return 1;
}



int _decide_hillslope_id(unsigned char cur_dir, unsigned char hs_dir, unsigned char upper_stream_dir_List[], int upper_stream_num,
						 int stream_id, int min_stream_id, int max_stream_id) {

	/* 对应只有一个上游河道像元的情况 */
	if (upper_stream_num == 1) {
		uint8 upper_stream_dir = upper_stream_dir_List[0];

		// 顺时针方向没有套圈
		// 沿着顺时针方向寻找右边坡
		if (cur_dir < upper_stream_dir) {
			if (hs_dir > cur_dir && hs_dir < upper_stream_dir) {
				return max_stream_id + (stream_id - min_stream_id) * 3 + 2; // 右边坡
			}
			else {
				return max_stream_id + (stream_id - min_stream_id) * 3 + 3; // 左边坡
			}
		}
		// 逆时针方向没有套圈
		// 沿着逆时针方向寻找左边坡
		else {
			if (hs_dir < cur_dir && hs_dir > upper_stream_dir) {
				return max_stream_id + (stream_id - min_stream_id) * 3 + 3; // 左边坡
			}
			else {
				return max_stream_id + (stream_id - min_stream_id) * 3 + 2; // 右边坡
			}
		}
	}

	/* 对应有多个上游河道像元的情况 */
	else {

		uint8 temp_dir = cur_dir;
		int encounter_channel_num = 0;
	
		if (temp_dir == 128) {
			temp_dir = 1;
		}
		else {
			temp_dir *= 2;
		}
		
		while (temp_dir != hs_dir) {
			if (_check_dir_in_upper_stream(temp_dir, upper_stream_dir_List, upper_stream_num)) {
				encounter_channel_num++;
			}
			
			if (temp_dir == 128) {
				temp_dir = 1;
			}
			else {
				temp_dir *= 2;
			}
		}
		
		if (encounter_channel_num == 0) {
			return max_stream_id + (stream_id - min_stream_id) * 3 + 2; // 右边坡
		}
		else if (encounter_channel_num == upper_stream_num) {
			return max_stream_id + (stream_id - min_stream_id) * 3 + 3; // 左边坡
		}
		else {
			return max_stream_id + (stream_id - min_stream_id) * 3 + 1; // 暂定为头坡
		}
	}
}


int _check_dir_in_upper_stream(unsigned char dir, unsigned char upper_stream_dir_List[], int upper_stream_num) {

	for (int q = 0; q < upper_stream_num; q++) {
		if (dir == upper_stream_dir_List[q]) {
			return 1;
		}
	}
	return 0;
}







int _check_on_mainstream(int t_ridx, int t_cidx, int inlet_ridx, int inlet_cidx, unsigned char inlet_dir, unsigned char* dir, int cols) {

	uint8 temp_dir = 0;
	uint64 t_idx = t_ridx * (uint64)cols + t_cidx;
	uint64 inlet_idx = inlet_ridx * (uint64)cols + inlet_cidx;
	inlet_idx = _get_down_idx64(inlet_dir, inlet_idx, cols);

	while (inlet_idx != 0)
	{
		if (inlet_idx == t_idx) {
			return 1;
		}
		inlet_idx = _get_down_idx64(dir[inlet_idx], inlet_idx, cols);

	}
	return 0;
}










//int _find_dir_index(unsigned char fdir, const unsigned char index_table[]) {
//
//	for (int p = 0; p < 8; p++) {
//		if (fdir == index_table[p]) {
//			return p;
//		}
//	}
//	return -1;
//}


//
//
///**********************
// *	循环法找左右边坡  *
// **********************/
//
//int end_flag = 0; // 标记左右循环时是否遇到河道
//int dir_probe = -1, next_dir_probe = -1; // 记录流向在数组中的索引
//int left_hillslope_id = 0, right_hillslope = 0;
//
//
//cur_dir = dir[idx];
//dir_probe = _find_dir_index(cur_dir, fdc);
//if (dir_probe < 0 || dir_probe > 7) {
//	fprintf(stderr, "Unexpected flow direction %d", cur_dir);
//	exit(-1);
//}
//
//// 先顺时针方向找右边坡
//next_dir_probe = dir_probe;
//while (end_flag == 0) {
//	next_dir_probe = next_dir_probe + 1;
//	if (next_dir_probe > 7) {
//		next_dir_probe = 0;
//	}
//
//	upper_idx = idx + offset[7 - next_dir_probe];
//	if (stream[upper_idx] >= min_channel_id) {
//		end_flag = 1;
//	}
//	else {
//		stack.List[0] = upper_idx;
//		stack.length = 1;
//		hillslope_id = max_channel_id + (stream_id - min_channel_id) * 3 + 2;
//		while (stack.length > 0) {
//			temp_idx = stack.List[--stack.length];
//			reverse_fdir = re_dir[temp_idx];
//			stream[temp_idx] = hillslope_id;
//			for (int p = 0; p < 8; p++) {
//				if (reverse_fdir >= div[p]) {
//					reverse_fdir -= div[p];
//					upper_idx = temp_idx + offset[p];
//					u64_List_append(&stack, upper_idx);
//				}
//			}
//		}
//
//	}
//}
//
//
//int left_channel_id = 0;
//end_flag = 0;
//// 逆时针方向找左边坡
//next_dir_probe = dir_probe - 1;
//if (next_dir_probe < 0) {
//	dir_probe = 7;
//}
//// 找一个来回
//while (next_dir_probe != dir_probe) {
//
//	upper_idx = idx + offset[7 - next_dir_probe];
//	// 还处于找左边坡的阶段
//	if (end_flag == 0) {
//
//		// 遇到河道
//		if (stream[upper_idx] >= min_channel_id) {
//			end_flag = 1;
//			left_channel_id = stream[upper_idx];
//		}
//		else {
//			stack.List[0] = upper_idx;
//			stack.length = 1;
//			hillslope_id = max_channel_id + (stream_id - min_channel_id) * 3 + 3;
//			while (stack.length > 0) {
//				temp_idx = stack.List[--stack.length];
//				reverse_fdir = re_dir[temp_idx];
//				stream[temp_idx] = hillslope_id;
//				for (int p = 0; p < 8; p++) {
//					if (reverse_fdir >= div[p]) {
//						reverse_fdir -= div[p];
//						upper_idx = temp_idx + offset[p];
//						u64_List_append(&stack, upper_idx);
//					}
//				}
//			}
//		}
//	}
//
//	// 将夹在上游河道之间的部分划归到左侧上游河道的右边坡
//	else {
//
//		if (stream[upper_idx] >= min_channel_id) {
//			left_channel_id = stream[upper_idx];
//		}
//		// 遇到非河道像元
//		else {
//			hillslope_id = max_channel_id + (left_channel_id - min_channel_id) * 3 + 2;
//			stack.List[0] = upper_idx;
//			stack.length = 1;
//			while (stack.length > 0) {
//				temp_idx = stack.List[--stack.length];
//				reverse_fdir = re_dir[temp_idx];
//				stream[temp_idx] = hillslope_id;
//				for (int p = 0; p < 8; p++) {
//					if (reverse_fdir >= div[p]) {
//						reverse_fdir -= div[p];
//						upper_idx = temp_idx + offset[p];
//						u64_List_append(&stack, upper_idx);
//					}
//				}
//			}
//		}
//
//	}
//
//	// 继续逆时针方向查找
//	next_dir_probe = dir_probe - 1;
//	if (next_dir_probe < 0) {
//		dir_probe = 7;
//	}
//}