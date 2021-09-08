#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "type_aka.h"
#include "get_reverse_fdir.h"
#include "pfs_origin.h"
#include "paint_up.h"
#include "paint_up_inner.h"


unsigned short* _dissolve_basin(unsigned char* dir, float* upa, float *dem, int rows, int cols, float ths, 
								unsigned long long outlet_idx, unsigned long long* sink_idxs, unsigned short sink_num) {


	// 初始化参数
	uint64 cols64 = (uint64)cols;
	uint64 total_num = rows * cols64;
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// 先计算逆流向
	uint8* re_dir = _get_re_dir(dir, rows, cols);

	// 先进行pfs编码
	unsigned short* basin = _pfs_o_uint16(re_dir, upa, rows, cols, ths, outlet_idx);


	// 判断内流域数量
	if (sink_num == 0) {
		;
	}
	else {
		double frac = 1.0 / 10;
		uint16* color = (uint16*)calloc(1, sizeof(unsigned short));
		if (color == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}
		*color = 10;
		_paint_up_uint16(sink_idxs, color, 1, frac, basin, re_dir, rows, cols);
		free(color);
		color = NULL;

		if (sink_num > 1) {
			uint16* colors = (uint16*)calloc(sink_num - 1, sizeof(unsigned short));
			if (colors == NULL) {
				fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
				exit(-1);
			}
			for (uint16 i = 1; i < sink_num; i++) {
				colors[i - 1] = 10 + i;
			}

			uint64* sink_idxs_b = (uint64*)calloc(sink_num - 1, sizeof(unsigned long long));
			if (sink_idxs_b == NULL) {
				fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
				exit(-1);
			}
			for (uint16 i = 1; i < sink_num; i++) {
				sink_idxs_b[i - 1] = sink_idxs[i];
			}

			uint64 p_stack_size = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
			if (p_stack_size > 100000000) {
				p_stack_size = 100000000;
			}
			_dissolve_sinks_uint16(basin, re_dir, dem, sink_idxs_b, colors, sink_num - 1, (uint16)11, cols, p_stack_size);
		}
	}
	return basin;
}


unsigned char* _pfs_o_uint8(unsigned char* dir, float* upa, int rows, int cols, float ths, unsigned long long outlet_idx) {

	// 初始化
	uint64 cols64 = (uint64)cols;
	uint64 total_num = rows * cols64;
	uint64 idx = outlet_idx;
	uint64 upper_idx = 0;;
	uint8 reverse_dir = 0;
	float temp_upa = 0.0;

	Tribu main_tribus[4];
	memset(main_tribus, 0, sizeof(main_tribus));
	float min_upa = 0.0;  // 最小支流的集水区面积
	int min_upa_probe = 0;  // 最小支流在数组中的位置
	float upa_ths[2] = { 0.0,0.0 }; // 存储干流和支流的集水区面积
	uint64 mt_idx[2] = { 0,0 }; // 存储干支流划分时，干流和支流出水口的位置索引

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	
	uint8* basin = (uint8*)calloc(total_num, sizeof(unsigned char));
	if (basin == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	
	// 先计算逆流向
	uint8* re_dir = _get_re_dir(dir, rows, cols);

	// 从出水口往上游追踪
	while (upa[idx] >= ths) {
		reverse_dir = re_dir[idx];
		if (reverse_dir == 0) {
			break; // 到达流域边界，则退出循环
		}
		for (int p = 0; p < 8; p++) {
			// 判断是否为上游
			if (reverse_dir >= div[p]) {
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
				reverse_dir -= div[p];
			}
		}

		// 如果存在支流
		if (mt_idx[1] != 0) {
			// 如果大于已知的最小支流，则进行插入操作
			if (upa_ths[1] > min_upa) {
				_tribu_insert(main_tribus, upa_ths[1], mt_idx[1],mt_idx[0], &min_upa, &min_upa_probe);
			}
		}
		idx = mt_idx[0];
		memset(upa_ths, 0, sizeof(upa_ths));
		memset(mt_idx, 0, sizeof(mt_idx));	
	}
	
	// 判断有几个子流域
	uint8 tribu_num = 0;
	for (int i = 0; i < 4; i++) {
		if (main_tribus[i].upa != 0) {
			tribu_num ++;
		}
	}
	uint basin_num = 2 * tribu_num + 1;

	// 准备调色盘
	uint8* colors = (uint8*)calloc(basin_num, sizeof(unsigned char));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint8 i = 0; i < basin_num; i++) {
		colors[i] = i + 1;
	}
	// 准备画笔起始位置
	uint64* basin_outlets = (uint64*)calloc(basin_num, sizeof(unsigned long long));
	if (basin_outlets == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	basin_outlets[0] = outlet_idx;
	uint8 probe = 1;
	for (uint8 i = 4 - tribu_num; i < 4; i++) {
		basin_outlets[probe] = main_tribus[i].tri_idx;
		probe++;
		basin_outlets[probe] = main_tribus[i].tru_idx;
	}

	// 如果流域被分成9份，先绘制下游流域，再绘制上游流域，要绘制 (21 / 9) * basin_size次
	// 如果要避免重复绘制，测需要先绘制上游流域，再绘制下游流域，还需引入baisn_size次比较运算，可能会更慢
	// 故采用第一种方案
	double compress = 1.0 / 3; // 默认栈大小为整幅影像的1/3
	_paint_up_uint8(basin_outlets, colors, basin_num, compress, basin, re_dir, rows, cols);

	return basin;

}



unsigned short* _pfs_o_uint16(unsigned char* re_dir, float* upa, int rows, int cols, float ths, unsigned long long outlet_idx) {

	// 初始化
	uint64 cols64 = (uint64)cols;
	uint64 total_num = rows * cols64;
	uint64 idx = outlet_idx;
	uint64 upper_idx = 0;;
	uint8 reverse_dir = 0;
	float temp_upa = 0.0;

	Tribu main_tribus[4];
	memset(main_tribus, 0, sizeof(main_tribus));
	float min_upa = 0.0;  // 最小支流的集水区面积
	int min_upa_probe = 0;  // 最小支流在数组中的位置
	float upa_ths[2] = { 0.0,0.0 }; // 存储干流和支流的集水区面积
	uint64 mt_idx[2] = { 0,0 }; // 存储干支流划分时，干流和支流出水口的位置索引

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	uint16* basin = (uint16*)calloc(total_num, sizeof(unsigned short));
	if (basin == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}


	// 从出水口往上游追踪
	while (upa[idx] >= ths) {
		reverse_dir = re_dir[idx];
		if (reverse_dir == 0) {
			break; // 到达流域边界，则退出循环
		}
		for (int p = 0; p < 8; p++) {
			// 判断是否为上游
			if (reverse_dir >= div[p]) {
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
				reverse_dir -= div[p];
			}
		}

		// 如果存在支流
		if (mt_idx[1] != 0) {
			// 如果大于已知的最小支流，则进行插入操作
			if (upa_ths[1] > min_upa) {
				_tribu_insert(main_tribus, upa_ths[1], mt_idx[1], mt_idx[0], &min_upa, &min_upa_probe);
			}
		}
		idx = mt_idx[0];
		memset(upa_ths, 0, sizeof(upa_ths));
		memset(mt_idx, 0, sizeof(mt_idx));
	}

	// 判断有几个子流域
	uint8 tribu_num = 0;
	for (int i = 0; i < 4; i++) {
		if (main_tribus[i].upa != 0) {
			tribu_num++;
		}
	}
	uint8 basin_num = 2 * tribu_num + 1;

	// 准备调色盘
	uint16* colors = (uint16*)calloc(basin_num, sizeof(unsigned char));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint8 i = 0; i < basin_num; i++) {
		colors[i] = i + 1;
	}
	// 准备画笔起始位置
	uint64* basin_outlets = (uint64*)calloc(basin_num, sizeof(unsigned long long));
	if (basin_outlets == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	basin_outlets[0] = outlet_idx;
	uint8 probe = 1;
	for (uint8 i = 4 - tribu_num; i < 4; i++) {
		basin_outlets[probe] = main_tribus[i].tri_idx;
		probe++;
		basin_outlets[probe] = main_tribus[i].tru_idx;
	}

	// 如果流域被分成9份，先绘制下游流域，再绘制上游流域，要绘制 (21 / 9) * basin_size次
	// 如果要避免重复绘制，测需要先绘制上游流域，再绘制下游流域，还需引入baisn_size次比较运算，可能会更慢
	// 故采用第一种方案
	double compress = 1.0 / 3; // 默认栈大小为整幅影像的1/3
	_paint_up_uint16(basin_outlets, colors, basin_num, compress, basin, re_dir, rows, cols);

	return basin;
}



unsigned char* _pfs_r_uint8(unsigned char* re_dir, float* upa, int rows, int cols, float ths, 
	unsigned long long outlet_idx, unsigned int* r_ridxs, unsigned int* r_cidxs, unsigned char* r_num) {

	// 初始化
	uint64 cols64 = (uint64)cols;
	uint64 total_num = rows * cols64;
	uint64 idx = outlet_idx;
	uint64 upper_idx = 0;;
	uint8 reverse_dir = 0;
	float temp_upa = 0.0;

	Tribu main_tribus[4];
	memset(main_tribus, 0, sizeof(main_tribus));
	float min_upa = 0.0;  // 最小支流的集水区面积
	int min_upa_probe = 0;  // 最小支流在数组中的位置
	float upa_ths[2] = { 0.0,0.0 }; // 存储干流和支流的集水区面积
	uint64 mt_idx[2] = { 0,0 }; // 存储干支流划分时，干流和支流出水口的位置索引

	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	uint8* basin = (uint8*)calloc(total_num, sizeof(unsigned char));
	if (basin == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	fprintf(stderr, "1  ");

	// 从出水口往上游追踪
	while (upa[idx] >= ths) {
		reverse_dir = re_dir[idx];
		if (reverse_dir == 0) {
			break; // 到达流域边界，则退出循环
		}
		for (int p = 0; p < 8; p++) {
			// 判断是否为上游
			if (reverse_dir >= div[p]) {
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
				reverse_dir -= div[p];
			}
		}

		// 如果存在支流
		if (mt_idx[1] != 0) {
			// 如果大于已知的最小支流，则进行插入操作
			if (upa_ths[1] > min_upa) {
				_tribu_insert(main_tribus, upa_ths[1], mt_idx[1], mt_idx[0], &min_upa, &min_upa_probe);
			}
		}
		idx = mt_idx[0];
		memset(upa_ths, 0, sizeof(upa_ths));
		memset(mt_idx, 0, sizeof(mt_idx));
	}
	fprintf(stderr, "2  ");

	// 判断有几个子流域
	uint8 tribu_num = 0;
	for (int i = 0; i < 4; i++) {
		if (main_tribus[i].upa != 0) {
			tribu_num++;
		}
	}
	uint basin_num = 2 * tribu_num + 1;

	// 准备调色盘
	uint8* colors = (uint8*)calloc(basin_num, sizeof(unsigned char));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint8 i = 0; i < basin_num; i++) {
		colors[i] = i + 1;
	}
	// 准备画笔起始位置
	uint64* basin_outlets = (uint64*)calloc(basin_num, sizeof(unsigned long long));
	if (basin_outlets == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	basin_outlets[0] = outlet_idx;
	uint8 probe = 1;
	for (uint8 i = 4 - tribu_num; i < 4; i++) {
		basin_outlets[probe] = main_tribus[i].tri_idx;
		probe++;
		basin_outlets[probe] = main_tribus[i].tru_idx;
		probe++;
	}

	// 如果流域被分成9份，先绘制下游流域，再绘制上游流域，要绘制 (21 / 9) * basin_size次
	// 如果要避免重复绘制，测需要先绘制上游流域，再绘制下游流域，还需引入baisn_size次比较运算，可能会更慢
	// 故采用第一种方案
	double compress = 1.0 / 10; // 默认栈大小为整幅影像的1/10
	_paint_up_uint8(basin_outlets, colors, basin_num, compress, basin, re_dir, rows, cols);

	// 返回子流域出水口信息
	*r_num = basin_num;
	for (uint8 i = 0; i < basin_num; i++) {
		r_ridxs[i] = (uint)(basin_outlets[i] / cols64);
		r_cidxs[i] = (uint)(basin_outlets[i] % cols64);
	}
	fprintf(stderr, "3\r\n");

	return basin;
}








int _tribu_insert(Tribu src[], float upa, unsigned long long tribu_idx, unsigned long long trunk_idx, float* min_upa, int* min_upa_probe) {

	// 在插入位置之后的元素全部向前移一位
	for (int i = *min_upa_probe; i < 3; i++) {
		src[i].upa = src[i + 1].upa;
		src[i].tri_idx = src[i + 1].tri_idx;
		src[i].tru_idx = src[i + 1].tru_idx;
	}
	
	// 在最后一位插入
	src[3].upa = upa;
	src[3].tri_idx = tribu_idx;
	src[3].tru_idx = trunk_idx;
	
	// 重新寻找最小的支流
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

