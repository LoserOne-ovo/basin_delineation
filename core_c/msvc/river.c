#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include "Array.h"
#include "get_reverse_fdir.h"
#include "paint_up.h"
#include "river.h"



int32_t* _dfn_stream(uint8_t* __restrict dir, float* __restrict upa, float ths, int32_t outlet_ridx, int32_t outlet_cidx, int32_t rows, int32_t cols) {


	uint64_t total_num = rows * (uint64_t)cols;
	uint64_t idx = 0, upper_idx = 0;
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };

	// 初始化结果
	int32_t* __restrict result = (int32_t*)calloc(total_num, sizeof(int32_t));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// 计算逆流向
	uint8_t* re_dir = _get_re_dir(dir, rows, cols);


	/* 深度遍历为每一个河道进行赋值*/

	// 辅助变量
	uint8_t reverse_fdir = 0;
	int32_t channel_id = 10001;
	uint8_t upper_channel_num = 0;
	uint64_t temp_upper_List[8] = { 0 };
	
	// 预设河段的规模为100000
	int32_t bench_channel_num = 100000;
	// 还是使用栈数据结构
	u64_DynArray streams = { 0,0, bench_channel_num, NULL };
	streams.data = (uint64_t*)calloc(bench_channel_num, sizeof(uint64_t));
	if (streams.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// 计算流域出口一维索引
	idx = (uint64_t)(outlet_ridx * (uint64_t)cols + outlet_cidx);
	streams.data[0] = idx;
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
			for (int32_t p = 0; p < 8; p++) {
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
				for (int32_t q = 0; q < upper_channel_num; q++) {
					u64_DynArray_Push(&streams, temp_upper_List[q]);
				}
				idx = streams.data[streams.length - 1];
				channel_id++;
			}

			// 如果没有上游河道像元，说明河段结束
			else {
				streams.length--;
				if (streams.length > 0) {
					idx = streams.data[streams.length - 1];
					channel_id++;
				}
				// 如果栈中没有其他河道，则退出循环
				else {
					break;
				}
			}
		}

	}


	free(streams.data);
	streams.data = NULL;
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
int32_t _dfn_stream_overlap_lake(int32_t* __restrict lake, uint8_t* __restrict dir, float* __restrict upa, 
	float ths, int32_t outlet_ridx, int32_t outlet_cidx, int32_t rows, int32_t cols) {


	uint64_t idx = 0, upper_idx =0;
	uint64_t total_num = rows * (uint64_t)cols;

	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };

	// 计算逆流向
	uint8_t* re_dir = _get_re_dir(dir, rows, cols);

	/* 深度遍历为每一个河道进行赋值*/

	// 辅助变量
	uint8_t reverse_fdir = 0;
	int32_t channel_id = 10000;
	uint8_t upper_channel_num = 0;
	uint64_t temp_upper_List[8] = { 0 };
	int32_t channel_end_flag = 0;

	// 预设河段的规模为100000
	int32_t bench_channel_num = 100000;
	// 还是使用栈数据结构
	u64_DynArray streams = { 0,0, bench_channel_num, NULL };
	streams.data = (uint64_t*)calloc(bench_channel_num, sizeof(uint64_t));
	if (streams.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// 计算流域出口一维索引
	idx = (uint64_t)(outlet_ridx * (uint64_t)cols + outlet_cidx);
	streams.data[0] = idx;
	streams.length = 1;

	// 如果流域出口处的汇流累积量小于阈值
	if (upa[idx] <= ths) {
		fprintf(stderr, "Flow accumulation of the outlet is less than the threshold!\r\n");
	}
	
	// 正常计算
	else {

		while (streams.length > 0) {

			idx = streams.data[--streams.length];
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
					for (int32_t p = 0; p < 8; p++) {
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
							u64_DynArray_Push(&streams, upper_idx);
							channel_end_flag = 1;
						}

					}
					// 如果上游有多个河道像元,则结束当前河段，添加新河段
					else if (upper_channel_num > 1) {
						for (uint8_t q = 0; q < upper_channel_num; q++) {
							u64_DynArray_Push(&streams, temp_upper_List[q]);
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
					for (int32_t p = 0; p < 8; p++) {
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
							u64_DynArray_Push(&streams, upper_idx);
							channel_end_flag = 1;
						}

					}
					// 如果上游有多个河道像元,则结束当前河段，添加新河段
					else if (upper_channel_num > 1) {
						for (uint8_t q = 0; q < upper_channel_num; q++) {
							u64_DynArray_Push(&streams, temp_upper_List[q]);
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

	free(streams.data);
	streams.data = NULL;
	streams.length = 0;
	streams.batch_size = 0;
	streams.alloc_length = 0;

	free(re_dir);
	re_dir = NULL;

	return 1;

}



// 绘制河道的山坡单元
int32_t _paint_river_hillslope_int32(int32_t* __restrict stream, int32_t min_channel_id, int32_t max_channel_id, uint8_t* __restrict dir, uint8_t* __restrict re_dir, int32_t rows, int32_t cols) {


	/**************************
	 *      初始化参数        *
	 **************************/
	
	
	// 经验参数
	int32_t bench_size = 100000;

	// 常量
	uint64_t total_num = rows * (uint64_t)cols;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	//const uint8_t fdc[8] = { 1,2,4,8,16,32,64,128 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// 辅助变量
	uint64_t idx = 0, temp_idx = 0, upper_idx = 0;
	uint8_t reverse_fdir = 0, temp_reverse_fdir = 0;
	uint8_t cur_dir = 0;
	uint8_t upper_channel_num = 0, upper_hs_num = 0;
	int32_t hillslope_id = 0, channel_id = 0;
	uint8_t cur_idx = 0;

	// 辅助列表
	uint64_t temp_upper_idx_List[8] = { 0 };
	uint8_t temp_upper_dir_List[8] = { 0 };
	uint8_t temp_upper_stream_dir_List[8] = { 0 };
	
	// 辅助栈
	u64_DynArray stack = { 0,0,bench_size,NULL };
	stack.data = (uint64_t*)calloc(bench_size, sizeof(uint64_t));
	if (stack.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}


	/**************************
	 *      绘制河道坡面      *
     **************************/


	uint64_t count = 0;


	// 循环整幅影像
	for (idx = 0; idx < total_num; idx++) {

		channel_id = stream[idx];


		// 如果是河道像元
		if (channel_id >= min_channel_id && channel_id <= max_channel_id) {

			count++;


			// 重置辅助变量
			upper_channel_num = upper_hs_num = 0;
			reverse_fdir = re_dir[idx];

			// 计算当前像元的上游河道数量和索引
			for (int32_t p = 0; p < 8; p++) {
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
				for (int32_t q = 0; q < upper_hs_num; q++) {
					_paint_upper_int32(temp_upper_idx_List[q], hillslope_id, &stack, stream, re_dir, offset, div);
				}
			}
			else {

				// 如果是入海口，找一个海洋像元，定位流向
				if (cur_dir == 0) {
					
					for (uint8_t p = 0; p < 8; p++) {
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
					for (int32_t q = 0; q < upper_hs_num; q++) {
						_paint_upper_int32(temp_upper_idx_List[q], hillslope_id, &stack, stream, re_dir, offset, div);
					}
				}


				/* 2.河道中央（只有一个上游）*/
				else if (upper_channel_num == 1) {

					for (int32_t q = 0; q < upper_hs_num; q++) {
						hillslope_id = _decide_hillslope_id(cur_dir, temp_upper_dir_List[q], temp_upper_stream_dir_List,
							upper_channel_num, channel_id, min_channel_id, max_channel_id);
						_paint_upper_int32(temp_upper_idx_List[q], hillslope_id, &stack, stream, re_dir, offset, div);
					}
				}


				/* 2.河道交叉（多个上游）*/
				else {
					cur_dir = dir[idx];
					for (int32_t q = 0; q < upper_hs_num; q++) {
						hillslope_id = _decide_hillslope_id(cur_dir, temp_upper_dir_List[q], temp_upper_stream_dir_List,
							upper_channel_num, channel_id, min_channel_id, max_channel_id);
						_paint_upper_int32(temp_upper_idx_List[q], hillslope_id, &stack, stream, re_dir, offset, div);
					}
				}
			}
		}
	}

	// 释放资源
	free(re_dir);
	re_dir = NULL;
	free(stack.data);
	stack.data = NULL;
	stack.alloc_length = 0;
	stack.length = 0;

	return 1;
}



int32_t _decide_hillslope_id(uint8_t cur_dir, uint8_t hs_dir, uint8_t upper_stream_dir_List[], int32_t upper_stream_num,
						 int32_t stream_id, int32_t min_stream_id, int32_t max_stream_id) {

	/* 对应只有一个上游河道像元的情况 */
	if (upper_stream_num == 1) {
		uint8_t upper_stream_dir = upper_stream_dir_List[0];

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

		uint8_t temp_dir = cur_dir;
		int32_t encounter_channel_num = 0;
	
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


int32_t _check_dir_in_upper_stream(uint8_t dir, uint8_t upper_stream_dir_List[], int32_t upper_stream_num) {

	for (int32_t q = 0; q < upper_stream_num; q++) {
		if (dir == upper_stream_dir_List[q]) {
			return 1;
		}
	}
	return 0;
}


int32_t _check_on_mainstream(int32_t t_ridx, int32_t t_cidx, int32_t inlet_ridx, int32_t inlet_cidx, uint8_t inlet_dir, uint8_t* dir, int32_t cols) {

	uint8_t temp_dir = 0;
	uint64_t t_idx = t_ridx * (uint64_t)cols + t_cidx;
	uint64_t inlet_idx = inlet_ridx * (uint64_t)cols + inlet_cidx;
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



/********************************************
 *      子流域内部划分左右边坡和源头坡      *
 ********************************************/
int32_t _delineate_basin_hillslope(uint8_t* __restrict stream, uint8_t* __restrict dir, 
	int32_t rows, int32_t cols, uint8_t nodata) {


	/**************************
	 *      初始化参数        *
	 **************************/

	 // 经验参数
	int32_t bench_size = 100000;

	// 常量
	uint64_t total_num = rows * (uint64_t)cols;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	//const uint8_t fdc[8] = { 1,2,4,8,16,32,64,128 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// 辅助变量
	uint64_t idx = 0, temp_idx = 0, upper_idx = 0;
	uint8_t reverse_fdir = 0, temp_reverse_fdir = 0;
	uint8_t cur_dir = 0, hs_dir = 0, upper_stream_dir = 0;
	uint8_t upper_channel_num = 0, upper_hs_num = 0;
	uint8_t hillslope_id = 0;
	uint8_t head_slope_flag = 0;
	uint8_t p = 0, q = 0;

	// 辅助列表
	uint64_t temp_upper_idx_List[8] = { 0 };
	uint8_t temp_upper_dir_List[8] = { 0 };
	uint8_t temp_upper_stream_dir_List[8] = { 0 };

	// 辅助栈
	u64_DynArray* stack = u64_DynArray_Initial(bench_size);
	
	// 计算逆流向矩阵
	uint8_t* re_dir = _get_re_dir(dir, rows, cols);

	/********************************************
	 *      子流域内部划分左右边坡和源头坡      *
	 ********************************************/

	// 循环整幅影像
	for (idx = 0; idx < total_num; idx++) {
		// 如果当前像元是河道像元
		if (stream[idx] == 1) {

			// 重置辅助变量
			upper_channel_num = upper_hs_num = 0;
			reverse_fdir = re_dir[idx];
			cur_dir = dir[idx];

			// 计算当前像元的上游河道像元数量和坡面像元数量
			for (p = 0; p < 8; p++) {
				if (reverse_fdir & div[p]) {
					upper_idx = idx + offset[p];
					// 如果上游像元是一个河道，则记录该像元
					if (stream[upper_idx] == 1) {
						temp_upper_stream_dir_List[upper_channel_num++] = div[p];
					}
					else {
						temp_upper_dir_List[upper_hs_num] = div[p];
						temp_upper_idx_List[upper_hs_num++] = upper_idx;
					}
				}
			}
			
			// 判断单元像元是否是源头坡河像元
			// 8邻域范围内有nodata值，认定为非源头流域，无源头坡
			head_slope_flag = 0;
			if (upper_channel_num == 0) {
				head_slope_flag = 1;
				for (p = 0; p < 8; p++) {
					upper_idx = idx + offset[p];
					if (stream[upper_idx] == nodata) {
						head_slope_flag = 0;
						upper_stream_dir = div[p];
						break;
					}
				}
			}
			else {
				upper_stream_dir = temp_upper_stream_dir_List[0];
			}


			// 如果是入海口，找一个海洋像元，定位流向
			if (cur_dir == 0) {
				for (p = 0; p < 8; p++) {
					temp_idx = idx + offset[p];
					if (dir[temp_idx] == nodata) {
						cur_dir = div[p];
						break;
					}
				}
			}

			// 划分源头坡
			// 如果是内流区终点,暂时当做源头坡处理
			if ((head_slope_flag == 1) || (cur_dir == 255)) {
				for (q = 0; q < upper_hs_num; q++) {
					hillslope_id = 4;
					_paint_upper_uint8(temp_upper_idx_List[q], hillslope_id, stack, stream, re_dir, offset, div);
				}
			}
			// 否则，划分左右边坡
			else {
				// 划分左右坡面
				for (q = 0; q < upper_hs_num; q++) {
					hs_dir = temp_upper_dir_List[q];
					hillslope_id = _dertermine_hillslope_postition(cur_dir, hs_dir, upper_stream_dir);
					_paint_upper_uint8(temp_upper_idx_List[q], hillslope_id, stack, stream, re_dir, offset, div);
				}
			}
		}
	}

	// 释放资源
	free(re_dir);
	re_dir = NULL;
	u64_DynArray_Destroy(stack);
	stack = NULL;

	return 1;
}


uint8_t _dertermine_hillslope_postition(uint8_t cur_dir, uint8_t hs_dir, uint8_t upper_stream_dir) {

	// 顺时针方向没有套圈
	// 沿着顺时针方向寻找右边坡
	if (cur_dir < upper_stream_dir) {
		if (hs_dir > cur_dir && hs_dir < upper_stream_dir) {
			return 2; // 右边坡
		}
		else {
			return 3; // 左边坡
		}
	}
	// 逆时针方向没有套圈
	// 沿着逆时针方向寻找左边坡
	else {
		if (hs_dir < cur_dir && hs_dir > upper_stream_dir) {
			return 3; // 左边坡
		}
		else {
			return 2; // 右边坡
		}
	}

}


