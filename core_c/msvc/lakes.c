#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "Array.h"
#include "get_reverse_fdir.h"
#include "paint_up.h"
#include "lakes.h"



/********************************
 *          ��������            *
 ********************************/

 // ������������
int32_t _correct_lake_network_int32(int32_t* __restrict lake, uint8_t* __restrict dir, uint8_t* __restrict re_dir, 
	float* __restrict upa, float ths, int32_t rows, int32_t cols) {

	uint64_t idx = 0;
	uint64_t upper_idx = 0, down_idx = 0;
	int32_t lake_value = 0;

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };


	// ��������
	for (int32_t i = 0; i < rows; i++) {
		for (int32_t j = 0; j < cols; j++) {

			// �������Ԫ�Ǻ�����Ԫ�������ں�����
			if (lake[idx] == 0 && upa[idx] > ths) {

				// ������Ԫ����
				upper_idx = idx;
				down_idx = _get_down_idx64(dir[idx], idx, cols);
				lake_value = lake[down_idx];

				// ���������Ԫ��������һ�����������º�����Χ���п��ܱ��ֲ��䣩
				if (down_idx != 0 && lake_value > 0) {
					_update_lake(upper_idx, down_idx, lake_value, lake, re_dir, upa, ths, cols, div, offset);
				}
			}
			idx++;
		}
	}

	return 1;
}


//  ��������������һ��һ����Ԫ���ݹ飩
int32_t _update_lake(uint64_t upper_idx, uint64_t down_idx, int32_t lake_value, int32_t* __restrict lake, uint8_t* __restrict re_dir, 
	float* __restrict upa, float ths, int32_t cols, const uint8_t div[], const int32_t offset[]) {

	uint64_t upper_i = 0, upper_j = 0, down_i = 0, down_j = 0;
	int32_t flag = 0;
	uint8_t reverse_fdir = 0;

	// �ж����κ����ڽ���Ԫ�Ƿ�Ϊ����
	down_i = down_idx / cols;
	down_j = down_idx % cols;
	upper_i = upper_idx / cols;
	upper_j = upper_idx % cols;

	// ������κӵ���Ԫ�����κ�����Ԫˮƽ����
	if (upper_i == down_i) {
		// �ж����κӵ���Ԫ�����������Ƿ�Ϊ������Ԫ
		if (lake[upper_idx - cols] == lake_value || lake[upper_idx + cols] == lake_value) {
			lake[upper_idx] = lake_value;
			flag = 1;
		}
	}
	// ������κӵ���Ԫ�����κ�����Ԫ��ֱ����
	else if (upper_j == down_j) {
		// �ж����κӵ���Ԫ�����������Ƿ�Ϊ������Ԫ
		if (lake[upper_idx - 1] == lake_value || lake[upper_idx + 1] == lake_value) {
			lake[upper_idx] = lake_value;
			flag = 1;
		}
	}
	// ������κӵ���Ԫ�����κ�����Ԫ45�ȹ���
	else {
		// �ж����κӵ���Ԫ�����κ�����Ԫ�Ĺ����ڽ���Ԫ�Ƿ�Ϊ������Ԫ
		if (lake[upper_i * cols + down_j] == lake_value || lake[down_i * cols + upper_j] == lake_value)
		{
			lake[upper_idx] = lake_value;
			flag = 1;
		}
	}

	// ��������˺����ķ�Χ����ô�Ը��µ���ԪΪ���κ�����Ԫ������������Ԫ���ٴθ��º�����Χ���γɵݹ�
	if (flag == 1) {

		down_idx = upper_idx;
		reverse_fdir = re_dir[upper_idx];
		for (int32_t p = 0; p < 8; p++) {
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



// �������������� ����������������������Һ�������С����ֵ������κ����Լ����������֮�����е�����ϲ���������
int32_t _correct_lake_network_2_int32(int32_t* __restrict lake, uint8_t* __restrict dir, uint8_t* __restrict re_dir,
	float* __restrict upa, float ths, int32_t rows, int32_t cols) {


	/********************
	 *  ���������ʼ��  *
	 ********************/
	
	uint64_t idx = 0;
	uint64_t upper_idx = 0, down_idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	int32_t lake_value = 0;
	int32_t next_lake_value = 0;

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	
	// ����һ���������ͼ�㣬�����������
	int32_t* __restrict fill_layer = (int32_t*)malloc(total_num * sizeof(int32_t));
	if (fill_layer == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// ����ͼ�㣬Ѱ����Ҫ�����Ĳ���
	for (idx = 0; idx < total_num; idx++) {

		// �ҵ�������Ԫ�����������ں����⣬���Ǻ���
		lake_value = lake[idx];
		if (lake_value > 0) {

			down_idx = _get_down_idx64(dir[idx], idx, cols);
			if (upa[down_idx] > ths) {
				next_lake_value = _find_next_water_body_int32(down_idx, lake, dir, cols);

				// ������κ�����Ȼ���Լ��������������ӵ�
				if (next_lake_value == lake_value) {
					// �ȸ���ͼ��
					_copy_layer_int32(lake, fill_layer, total_num);
					// �ٽ�������
					_update_lake_bound_int32(idx, lake, fill_layer, dir, cols, lake_value);
				}

			}
		}
	}
	// �ͷ���Դ
	free(fill_layer);
	fill_layer = NULL;

	// ʹ�õ�һ�ַ�����������������
	_correct_lake_network_int32(lake, dir, re_dir, upa, ths, rows, cols);

	return 1;
}



int32_t _copy_layer_int32(int32_t* __restrict src, int32_t* __restrict dst, uint64_t total_num) {

	for (uint64_t idx = 0; idx < total_num; idx++) {
		dst[idx] = src[idx];
	}
	return 1;
}


// ���ں����ͺӵ�����ȫƥ��Ĳ��ֽ��д���������Ӻ�����������������ע��ú�����
// ��������ᵼ�º��������г���һЩ�ն���
// Ϊ�˱�������������Ѻӵ���������еĲ��ֱ��Ϊ������
int32_t _update_lake_bound_int32(uint64_t idx, int32_t* __restrict water, int32_t* __restrict new_layer, uint8_t* __restrict dir, int32_t cols, int32_t value) {

	/********************
	 *   �����������   *
	 ********************/

	int32_t down_water_id = 0;
	uint64_t down_idx = 0, local_idx = 0, temp_idx = 0;
	uint8_t upper_dir = 0, local_dir = 0, temp_dir = 0;

	int32_t left_flag = 1, right_flag = 1;
	uint64_t left_idx = 0, right_idx = 0;
	int32_t left_count = 0, right_count = 0;


	/******************
	 *   ������ʼ��   *
	 ******************/

	down_water_id = 0;
	down_idx = _get_down_idx64(dir[idx], idx, cols);
	local_dir = dir[idx];


	/************************************
	 *   �ںӵ��������������һ����Ԫ   *
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
	 *   �����޸ĺ�����Χ   *
	 ************************/

	 // ����ӵ�����������һ��û���ҵ����棬˵���ӵ������ź�����
	 // ֱ�ӰѺӵ����ɺ���
	if (left_flag || right_flag) {

		down_idx = _get_down_idx64(dir[idx], idx, cols);
		down_water_id = 0;

		while (down_water_id != value) {
			water[down_idx] = value;
			down_idx = _get_down_idx64(dir[down_idx], down_idx, cols);
			down_water_id = water[down_idx];
		}
	}

	// ������඼�ҵ������棬�ж���һ�������Ǽ��غӵ��ͺ����м�
	// ʹ����������㷨���ֱ����ӵ����࣬�ж���һ������������
	else {

		uint64_t overflow_num = 1000;
		int32_t offset_4[4] = { -1, 1, -cols, cols };
		int32_t i = 0;
		uint64_t offset_idx = 0;

		u64_DynArray seed = { 0,0,overflow_num, NULL };
		seed.data = (uint64_t*)calloc(seed.alloc_length, sizeof(uint64_t));
		if (seed.data == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}

		// ���
		seed.length = 0;
		seed.data[seed.length++] = left_idx;
		while (seed.length > 0 && left_count <= overflow_num) {
			temp_idx = seed.data[--seed.length];
			new_layer[temp_idx] = value;
			left_count++;

			for (i = 0; i < 4; i++) {
				offset_idx = temp_idx + offset_4[i];
				if (new_layer[offset_idx] == 0) {
					u64_DynArray_Push(&seed, offset_idx);
				}
			}
		}

		// �Ҳ�
		seed.length = 0;
		seed.data[seed.length++] = right_idx;
		while (seed.length > 0 && right_count < overflow_num) {
			temp_idx = seed.data[--seed.length];
			new_layer[temp_idx] = value;
			right_count++;

			for (i = 0; i < 4; i++) {
				offset_idx = temp_idx + offset_4[i];
				if (new_layer[offset_idx] == 0) {
					u64_DynArray_Push(&seed, offset_idx);
				}
			}
		}

		// ��ԭͼ������������
		if (left_count < overflow_num || right_count < overflow_num) {

			/**********************
			 *   �ȸı�ӵ���ֵ   *
			 **********************/

			down_idx = _get_down_idx64(dir[idx], idx, cols);
			down_water_id = 0;

			while (down_water_id != value) {
				water[down_idx] = value;
				down_idx = _get_down_idx64(dir[down_idx], down_idx, cols);
				down_water_id = water[down_idx];
			}

			/**************************
			 *   �ٸı����������ֵ   *
			 **************************/

			temp_idx = left_count <= right_count ? left_idx : right_idx;
			seed.length = 0;
			seed.data[seed.length++] = temp_idx;
			while (seed.length > 0 && left_count <= overflow_num) {
				temp_idx = seed.data[--seed.length];
				water[temp_idx] = value;

				for (i = 0; i < 4; i++) {
					offset_idx = temp_idx + offset_4[i];
					if (new_layer[offset_idx] == 0) {
						u64_DynArray_Push(&seed, offset_idx);
					}
				}
			}
		}
		else {
			; // �������������Ԫ������������ֵ��ֱ�Ӳ���
		}

		// �ͷ��ڴ�
		free(seed.data);
		seed.data = NULL;
		seed.length = 0;
		seed.alloc_length = 0;
	}

	return 1;
}





/********************************
 *          ��������            *
 ********************************/


// ׷�ٺ�������
int32_t _paint_up_lake_hillslope_int32(int32_t* __restrict lake, int32_t max_lake_id, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols) {

	uint64_t idx = 0, upper_idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	
	uint8_t reverse_fdir = 0;

	int32_t lake_value = 0; 
	int32_t lake_hs_id = 0; // ��������id

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };


	// ջ���������Ӱ���С�ı���
	double frac = 0.001;


	// ��ʼ������ջ
	uint64_t batch_size = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}

	u64_DynArray stack = { 0,0,batch_size,NULL };
	stack.data = (uint64_t*)calloc(batch_size, sizeof(uint64_t));
	if (stack.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = batch_size;

	for (idx = 0; idx < total_num; idx++) {

		lake_value = lake[idx];
		// �ж��Ƿ��Ǻ�����Ԫ
		if (lake_value > 0 && lake_value <= max_lake_id) {
			
			reverse_fdir = re_dir[idx];

			for (int32_t p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					
					upper_idx = idx + offset[p];
					// ���������������Ԫ����ʼ����׷������
					if (lake[upper_idx] == 0 && upa[upper_idx] < ths) {
						lake_hs_id = lake_value + max_lake_id;
						_paint_upper_unpainted_int32(upper_idx, lake_hs_id, &stack, lake, re_dir, offset, div);
					}
					reverse_fdir -= div[p];
				}
			}
		}
	}


	free(stack.data);
	stack.data = NULL;
	stack.length = 0;
	stack.alloc_length = 0;
	stack.batch_size = 0;

	return 1;
}



// ׷�ٺ������棬��������ͬһ�������ĺӶ�Ҳ���Ϊ���棨���û������������
int32_t _paint_up_lake_hillslope_2_int32(int32_t* __restrict lake, int32_t max_lake_id, uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols) {

	uint64_t idx = 0, upper_idx = 0, down_idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;

	uint8_t reverse_fdir = 0;

	int32_t lake_value = 0;
	int32_t lake_hs_id = 0; // ��������id
	int32_t next_water_id = 0;

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// ջ���������Ӱ���С�ı���
	double frac = 0.001;

	// ��ʼ������ջ
	uint64_t batch_size = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}

	u64_DynArray stack = { 0,0,batch_size,NULL };
	stack.data = (uint64_t*)calloc(batch_size, sizeof(uint64_t));
	if (stack.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = batch_size;

	
	/*********************
     *   ���ƺ�������    *
     *********************/

	for (idx = 0; idx < total_num; idx++) {
		lake_value = lake[idx];	
		// ����Ȳ��Ǻӵ�Ҳ���Ǻ���
		if (lake_value == 0 && upa[idx] < ths) {
			// ��������
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			// ����Ǻ���ע���
			if (lake[down_idx] > 0 && lake[down_idx] <= max_lake_id) {
				lake_hs_id = lake[down_idx] + max_lake_id;
				_paint_upper_unpainted_int32(idx, lake_hs_id, &stack, lake, re_dir, offset, div);
			}
		}
		// ����Ǻ���
		else if (lake_value > 0 && lake_value <= max_lake_id) {
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			// �����������
			if (down_idx != 0 && lake[down_idx] == 0) {
				// �ҵ�����ˮ�壬�ж��Ƿ�������������������
				next_water_id = _find_next_water_body_int32(down_idx, lake, dir, cols);
				// ��������������������棬��κӵ�����κӵ���������뵽����������
				if (next_water_id == lake_value || next_water_id == (lake_value + max_lake_id)) {
					lake_hs_id = lake_value + max_lake_id;
					while (lake[down_idx] == 0) {
						lake[down_idx] = lake_hs_id;
						reverse_fdir = re_dir[down_idx];

						// ��δ���ƵķǺӵ���Ԫ����
						for (int32_t p = 0; p < 8; p++) {
							if (reverse_fdir >= div[p]) {
								upper_idx = down_idx + offset[p];
								if (lake[upper_idx] == 0 && upa[upper_idx] < ths) {
									_paint_upper_unpainted_int32(upper_idx, lake_hs_id, &stack, lake, re_dir, offset, div);
								}
								reverse_fdir -= div[p];
							}
						}
						down_idx = _get_down_idx64(dir[down_idx], down_idx, cols);
					}	
				}
			}
		}
		// ���������
		else {
			;
		}
	}

	free(stack.data);
	stack.data = NULL;
	stack.length = 0;
	stack.alloc_length = 0;
	stack.batch_size = 0;

	return 1;
}



// ׷�ٺ������棬��������ͬһ�������ĺӶ�Ҳ���Ϊ���棨���û������������
int32_t _paint_up_lake_hillslope_3_int32(int32_t* __restrict lake, int32_t max_lake_id, uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols) {

	uint64_t idx = 0, upper_idx = 0, down_idx = 0;
	uint64_t inlet_idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;

	uint8_t reverse_fdir = 0;

	int32_t lake_value = 0;
	int32_t lake_hs_id = 0; // ��������id
	int32_t next_water_id = 0;

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// ջ���������Ӱ���С�ı���
	double frac = 0.001;

	// ��ʼ������ջ
	uint64_t batch_size = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}

	u64_DynArray stack = { 0,0,batch_size,NULL };
	stack.data = (uint64_t*)calloc(batch_size, sizeof(uint64_t));
	if (stack.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = batch_size;


	/*********************
	 *   ���ƺ�������    *
	 *********************/

	for (idx = 0; idx < total_num; idx++) {
		lake_value = lake[idx];
		// ����Ȳ��Ǻӵ�Ҳ���Ǻ���
		if (lake_value == 0 && upa[idx] < ths) {
			// ��������
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			// ����Ǻ���ע���
			if (lake[down_idx] > 0 && lake[down_idx] <= max_lake_id) {
				lake_hs_id = lake[down_idx] + max_lake_id;
				_paint_upper_unpainted_int32(idx, lake_hs_id, &stack, lake, re_dir, offset, div);
			}
		}
		// ����Ǻ���
		else if (lake_value > 0 && lake_value <= max_lake_id) {
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			// �����������
			if (down_idx != 0 && lake[down_idx] == 0 && upa[down_idx] > ths) {
				// �ҵ�����ˮ�壬�ж��Ƿ�������������������
				next_water_id = _find_next_water_body_int32(down_idx, lake, dir, cols);
				// ��������������������棬��κӵ�����κӵ���������뵽����������
				if (next_water_id == lake_value || next_water_id == (lake_value + max_lake_id)) {
					lake_hs_id = lake_value + max_lake_id;
					while (lake[down_idx] == 0) {
						lake[down_idx] = lake_hs_id;
						reverse_fdir = re_dir[down_idx];
						// ��δ���ƵķǺӵ���Ԫ����
						for (int32_t p = 0; p < 8; p++) {
							if (reverse_fdir >= div[p]) {
								upper_idx = down_idx + offset[p];
								if (lake[upper_idx] == 0 && upa[upper_idx] < ths) {
									_paint_upper_unpainted_int32(upper_idx, lake_hs_id, &stack, lake, re_dir, offset, div);
								}
								reverse_fdir -= div[p];
							}
						}
						down_idx = _get_down_idx64(dir[down_idx], down_idx, cols);
					}
				}

				// ���ͨ���ӵ������ĺ���
				else if (next_water_id > 0) {
					// ��������֮����������
					// ���С����ֵ����Ҳ��Ϊ������
					inlet_idx = _find_next_water_body_idx_int32(down_idx, lake, dir, cols);
					if ((upa[inlet_idx] - upa[down_idx]) < ths) {
						lake_hs_id = next_water_id > max_lake_id ? next_water_id : next_water_id + max_lake_id;
						fprintf(stderr, "%d\r\n", lake_hs_id);
						reverse_fdir = re_dir[inlet_idx];
						for (int32_t p = 0; p < 8; p++) {
							if (reverse_fdir >= div[p]) {
								upper_idx = inlet_idx + offset[p];
								if (lake[upper_idx] == 0) {
									_paint_upper_unpainted_int32(upper_idx, lake_hs_id, &stack, lake, re_dir, offset, div);
								}
								reverse_fdir -= div[p];
							}
						}
					}
				}
				else {
					;
				}
			}
		}
		// ���������
		else {
			;
		}
	}

	free(stack.data);
	stack.data = NULL;
	stack.length = 0;
	stack.alloc_length = 0;
	stack.batch_size = 0;

	return 1;
}




/********************************
 *          ��������            *
 ********************************/


// ׷�ٺ�����������
int32_t _paint_lake_local_catchment_int32(int32_t* __restrict lake, int32_t lake_num, uint8_t* __restrict re_dir, int32_t rows, int32_t cols) {

	uint64_t idx = 0, upper_idx = 0, temp_idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	uint8_t reverse_fdir = 0, sub_reverse_fdir = 0;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	int32_t lake_value = 0;

	// ջ���������Ӱ���С�ı���
	double frac = 0.001;
	// ��ʼ������ջ
	uint64_t batch_size = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}

	u64_DynArray stack = { 0,0,batch_size,NULL };
	stack.data = (uint64_t*)calloc(batch_size, sizeof(uint64_t));
	if (stack.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = batch_size;

	// ���ƺ�����������
	for (idx = 0; idx < total_num; idx++) {
		lake_value = lake[idx];
		// �������Ԫ�Ǻ���
		if (lake_value > 0 && lake_value <= lake_num) {
			reverse_fdir = re_dir[idx];
			// �ҵ��Ǻ���������
			for (int32_t p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					upper_idx = idx + offset[p];
					// ������Ǻ�����Ԫ����ʼ����׷�����棬ֱ��������������
					if (lake[upper_idx] == 0) {
						stack.data[0] = upper_idx;
						stack.length = 1;
						while (stack.length > 0) {
							temp_idx = stack.data[--stack.length];
							lake[temp_idx] = lake_value;
							sub_reverse_fdir = re_dir[temp_idx];
							for (int32_t p = 0; p < 8; p++) {
								if (sub_reverse_fdir >= div[p]) {
									sub_reverse_fdir -= div[p];
									upper_idx = temp_idx + offset[p];
									if (lake[upper_idx] == 0) {
										u64_DynArray_Push(&stack, upper_idx);
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

	free(stack.data);
	stack.data = NULL;
	stack.length = 0;
	stack.alloc_length = 0;
	stack.batch_size = 0;

	return 1;
}


// ׷�ٺ�����������
int32_t _paint_lake_upper_catchment_int32(int32_t* __restrict lake, int32_t lake_id, int32_t* __restrict board, uint8_t* __restrict re_dir, int32_t rows, int32_t cols) {


	uint64_t idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	uint64_t upper_idx = 0;
	uint8_t reverse_fdir = 0;

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// ջ���������Ӱ���С�ı���
	double frac = 0.001;
	uint64_t batch_size = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}
	// ��ʼ������ջ
	u64_DynArray stack = { 0,0,batch_size,NULL };
	stack.data = (uint64_t*)calloc(batch_size, sizeof(uint64_t));
	if (stack.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	stack.alloc_length = batch_size;

	for (idx = 0; idx < total_num; idx++) {

		if (lake[idx] == lake_id) {
			board[idx] = lake_id;
			reverse_fdir = re_dir[idx];
			// �ҵ��Ǻ���������
			for (int32_t p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					upper_idx = idx + offset[p];
					// ������β��Ǹú�������Ԫ
					if (lake[upper_idx] != lake_id) {
						_paint_upper_unpainted_int32(upper_idx, lake_id, &stack, board, re_dir, offset, div);
					}
					reverse_fdir -= div[p];
				}
			}
		}
	}


	free(stack.data);
	stack.data = NULL;
	stack.length = 0;
	stack.alloc_length = 0;
	stack.batch_size = 0;

	return 1;
}




/********************************
 *          ��������            *
 ********************************/

// ��������֮��������ι�ϵ
int32_t* _topology_between_lakes(int32_t* __restrict water, int32_t lake_num, int32_t* __restrict tag_array, uint8_t* __restrict dir, int32_t rows, int32_t cols) {

	uint64_t idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	uint64_t down_idx = 0;
	int32_t water_id = 0;
	int32_t next_down_id = 0;
	int32_t down_water_id = 0;
	int32_t default_down_lake_num = 10;

	// ����ռ�
	// ÿ�����������ж������
	i32_DynArray** down_lake_List = (i32_DynArray**)malloc(lake_num * sizeof(i32_DynArray*));
	if (down_lake_List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int32_t i = 0; i < lake_num; i++) {
		down_lake_List[i] = i32_DynArray_Initial(default_down_lake_num);
	}

	// Ѱ��ÿ������������
	for (idx = 0; idx < total_num; idx++) {
		water_id = water[idx];
		// ����Ǻ���
		if (water_id > 0) {
			// �ж��Ƿ��Ǻ����ڵ��������յ�
			// ��������ڵ��������յ㣬�����������id���뵽�����б���
			if (dir[idx] == 255) {
				if (!check_in_i32_DynArray(water_id, down_lake_List[water_id - 1])) {
					i32_DynArray_Push(down_lake_List[water_id - 1], water_id);
				}
				continue;
			}
			// ������Ǻ������жϸõ��Ƿ��Ǻ�����ˮ��
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			next_down_id = water[down_idx];	
			// ���λ������������˵�����Ǻ�����ˮ��
			if (next_down_id == water_id) {
				continue;
			}
			// ֱ�����β��Ǻ���
			else if (next_down_id == 0) {				
				// Ѱ�����κ���
				down_water_id = _find_next_water_body_int32(down_idx, water, dir, cols);
				// û�����κ�����������Ȼ���������
				if (down_water_id == 0 || down_water_id == water_id) {
					continue;
				}
				// ��������������������û�к������������յ�
				else {
					// ����Ƿ��Ѿ���¼���������
					if (!check_in_i32_DynArray(down_water_id, down_lake_List[water_id - 1])) {
						i32_DynArray_Push(down_lake_List[water_id - 1], down_water_id);
					}
				}
			}
			// ֱ����������������
			else if (next_down_id > 0) {
				if (!check_in_i32_DynArray(next_down_id, down_lake_List[water_id - 1])) {
					i32_DynArray_Push(down_lake_List[water_id - 1], next_down_id);
				}
			}
			// ������������
			else {
				continue;
			}
		}

		/****************************************
		 *  δ������ͨ����ˮ�ڵ����κ��������  *
		 *  �жϸó�ˮ���Ƿ��Ǻ��������ĳ�ˮ��  *
		 ****************************************/
	}


	// �������κ�����IDת��һά���鷵��
	int32_t total_down = 0;
	for (int32_t i = 0; i < lake_num; i++) {
		total_down += down_lake_List[i]->length;
		tag_array[i] = total_down;
	}
	
	int32_t insert_probe = 0;
	int32_t* result = (int32_t*)calloc(total_down, sizeof(int32_t));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int32_t i = 0; i < lake_num; i++) {
		for (int32_t j = 0; j < down_lake_List[i]->length; j++) {
			result[insert_probe++] = down_lake_List[i]->data[j];
		}
	}

	// �ͷ��ڴ�
	for (int32_t i = 0; i < lake_num; i++) {
		i32_DynArray_Destroy(down_lake_List[i]);
	}
	free(down_lake_List);
	down_lake_List = NULL;

	return result;
}


// Ѱ�����ε�ˮ�� 
/*
	���û���ҵ�����ˮ��( pixel_value > 0)�����ر���ֵ����������Ϊ0
	����ҵ�����ˮ�壬�򷵻�����ˮ��ı��
	���������һ���ֲ��ݵ㣬�Ҿֲ��ݵ㴦û��ˮ�壬�򷵻�-1
*/
int32_t _find_next_water_body_int32(uint64_t idx, int32_t* __restrict water, uint8_t* __restrict dir, int32_t cols) {

	uint64_t down_idx = idx;
	int32_t down_water_id = 0;
	uint8_t temp_dir = 0;

	do {
		// ����������Ԫλ��
		temp_dir = dir[down_idx];
		down_idx = _get_down_idx64(temp_dir, down_idx, cols);
		
		// ����Ҳ���������
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


uint64_t _find_next_water_body_idx_int32(uint64_t idx, int32_t* __restrict water, uint8_t* __restrict dir, int32_t cols) {

	uint64_t down_idx = idx;
	uint64_t temp_idx = 0;
	int32_t down_water_id = 0;
	uint8_t temp_dir = 0;

	do {
		// ����������Ԫλ��
		temp_dir = dir[down_idx];
		temp_idx = _get_down_idx64(temp_dir, down_idx, cols);

		// ����Ҳ���������
		if (temp_idx == 0) {
			if (temp_dir == 255) {
				return down_idx;
			}
			else {
				return 0;
			}
		}
		down_idx = temp_idx;
		down_water_id = water[down_idx];

	} while (down_water_id <= 0);

	return down_idx;
}






// ���D8����������Ǳ�ڵĺ�����ˮ��
int32_t _mark_lake_outlet_int32(int32_t* __restrict lake, int32_t min_lake_id, int32_t max_lake_id, uint8_t* __restrict dir, int32_t rows, int32_t cols) {

	uint64_t idx = 0, down_idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	uint8_t temp_dir = 0;
	int32_t lake_id = 0;

	for (idx = 0; idx < total_num; idx++) {

		lake_id = lake[idx];
		// ����Ǻ�����Ԫ���ж��Ƿ�Ϊ��������
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


// ��������֮�����·
uint64_t* _route_between_lake(int32_t* __restrict lake, int32_t lake_num, uint8_t* __restrict dir, float* __restrict upa, 
	int32_t rows, int32_t cols, int32_t* return_num, uint64_t* return_length) {


	uint64_t idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	uint64_t down_idx = 0;
	int32_t lake_id = 0;
	int32_t next_down_id = 0;
	int32_t down_lake_id = 0;


	lake_pour* lake_down_list = (lake_pour*)malloc(lake_num * sizeof(lake_pour));
	if (lake_down_list == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int32_t i = 0; i < lake_num; i++) {
		lake_down_list[i].num = 0;
		lake_down_list[i].data = NULL;
	}

	// �Ҹ�ÿ�������ĵ����κ����ĳ�ˮ�ڣ�һ�����κ���ֻ����һ����ˮ�ڣ�ȡ�����ۻ�������
	// ����һ�������ж�����κ���
	for (idx = 0; idx < total_num; idx++) {
		
		lake_id = lake[idx];
		// ����Ǻ���
		if (lake_id > 0) {
			// ����Ǻ����ڲ����������յ�
			if (dir[idx] == 255) {
				// �ں��������б��в����Լ�
				_insert_lake_down_water(&lake_down_list[lake_id - 1], lake_id, lake_id, idx, upa);
				continue;
			}

			//�ж��Ƿ��Ǻ�����ˮ��
			down_idx = _get_down_idx64(dir[idx], idx, cols);
			next_down_id = lake[down_idx];
			// ���λ����������
			if (next_down_id == lake_id) {
				continue;
			}
			// ���β��Ǻ���
			else if (next_down_id == 0) {
				// Ѱ�����κ���
				down_lake_id = _find_next_water_body_int32(down_idx, lake, dir, cols);
				// �������λ�����������ı�������
				if (down_lake_id > 0 && down_lake_id != lake_id) {
					_insert_lake_down_water(&lake_down_list[lake_id - 1], lake_id, down_lake_id, idx, upa);
				}
				// ������β�����ĳ����������λ��ĳ����������
				else if (down_lake_id == -1) {
					_insert_lake_down_water(&lake_down_list[lake_id - 1], lake_id, lake_id, idx, upa);
				}
				else {
					continue;
				}
			}
			// ��������������
			else if (next_down_id > 0) {
				_insert_lake_down_water(&lake_down_list[lake_id - 1], lake_id, next_down_id, idx, upa);
				continue;
			}
			// ������������
			else {
				continue;
			}
		}
	}


	// ͳ�ƺ���֮�����·������
	int32_t route_num = 0;
	for (int32_t i = 0; i < lake_num; i++) {
		if (lake_down_list[i].num > 0) {
			for (int32_t j = 0; j < lake_down_list[i].num; j++) {
				if (lake_down_list[i].data[j].upper_water != lake_down_list[i].data[j].down_water) {
					route_num += 1;
				}
			}
		}
	}

	// ��ʼ����·
	lake_route* routeList = (lake_route*)malloc(route_num * sizeof(lake_route));
	if (routeList == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (int32_t i = 0; i < route_num; i++) {
		routeList[i].upper_water = 0;
		routeList[i].down_water = 0;
		routeList[i].route.length = 0;
		routeList[i].route.batch_size = DEFAULT_PATH_LENGTH;
		routeList[i].route.data = (uint64_t*)calloc(DEFAULT_PATH_LENGTH, sizeof(uint64_t));
		if (routeList[i].route.data == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}
		routeList[i].route.alloc_length = DEFAULT_PATH_LENGTH;
	}

	// ������·
	int32_t route_id = 0;
	int32_t upper_id = 0;
	int32_t down_id = 0;
	uint64_t outlet_idx = 0;

	
	// ѭ����ȡ��·
	for (int32_t i = 0; i < lake_num; i++) {
		if (lake_down_list[i].num > 0) {
			for (int32_t j = 0; j < lake_down_list[i].num; j++) {
				upper_id = lake_down_list[i].data[j].upper_water;
				down_id = lake_down_list[i].data[j].down_water;
				outlet_idx = lake_down_list[i].data[j].outlet_idx;	
				// ��ȡ��·
				if (upper_id != down_id) {
					routeList[route_id].upper_water = upper_id;
					routeList[route_id].down_water = down_id;
					_extract_route(&routeList[route_id].route, down_id, outlet_idx, lake, dir, cols);
					route_id++;
				}
			}
		}
	}
	

	// ��һά�������ʽ���ظ�Python
	// ͳ�����鳤��
	uint64_t result_length = 0;
	for (int32_t i = 0; i < route_num; i++) {
		result_length += 3 + routeList[i].route.length;
	}
	// �����ڴ�
	uint64_t* result = (uint64_t*)calloc(result_length, sizeof(uint64_t));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	*return_num = route_num;
	*return_length = result_length;
	uint64_t offset = 0;
	// ��������
	for (int32_t i = 0; i < route_num; i++) {
		result[offset + 0] = (uint64_t)routeList[i].upper_water;
		result[offset + 1] = (uint64_t)routeList[i].down_water;
		result[offset + 2] = routeList[i].route.length;
		offset += 3;
		for (uint64_t m = 0; m < routeList[i].route.length; m++) {
			result[offset + m] = routeList[i].route.data[m];
		}
		offset += routeList[i].route.length;
	}
	

	// �ͷ��ڴ�
	for (int32_t i = 0; i < lake_num; i++) {
		if (lake_down_list[i].num > 0) {
			free(lake_down_list[i].data);
		}
	}
	free(lake_down_list);
	lake_down_list = NULL;
	
	for (int32_t i = 0; i < route_num; i++) {
		free(routeList[i].route.data);
	}
	free(routeList);
	routeList = NULL;


	return result;
}


int32_t _insert_lake_down_water(lake_pour* src, int32_t src_id, int32_t down_id, uint64_t outlet_idx, float* __restrict upa){

	// �ж��Ƿ��Ѿ����ڸ�����
	int32_t exist_flag = _check_lake_down_existed(src, down_id);
	// ��������ڣ�ֱ�Ӳ���
	if (exist_flag < 0){
		water_pour* newList = (water_pour*)realloc(src->data, (src->num + (uint64_t)DEFAULT_POUR_NUM) * sizeof(water_pour));
		if (newList == NULL) {
			fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
			exit(-1);
		}
		src->data = newList;
		src->data[src->num].upper_water = src_id;
		src->data[src->num].down_water = down_id;
		src->data[src->num].outlet_idx = outlet_idx;
		src->num++;
	}
	// ������ڣ�ȡ�����ۻ������ĳ�ˮ��
	else
	{
		if (upa[outlet_idx] > upa[src->data[exist_flag].outlet_idx]) {
			src->data[exist_flag].outlet_idx = outlet_idx;
		}
	}

	return 1;
}

int32_t _check_lake_down_existed(lake_pour* src, int32_t down_id) {

	for (int32_t i = 0; i < src->num; i++) {
		if (src->data[i].down_water == down_id) {
			return i;
		}
	}
	return -1;
}


int32_t _extract_route(u64_DynArray* src, int32_t down_water, uint64_t outlet_idx, int32_t* __restrict lake, uint8_t* __restrict dir, int32_t cols) {


	uint8_t upper_dir = 255;
	uint8_t temp_dir = 0;
	uint64_t temp_idx = outlet_idx;
	int32_t next_water_id = 0;

	do {
		temp_dir = dir[temp_idx];
		// ����·
		if (temp_dir != upper_dir) {
			u64_DynArray_Push(src, temp_idx);
			upper_dir = temp_dir;
		}
		temp_idx = _get_down_idx64(temp_dir, temp_idx, cols);
		next_water_id = lake[temp_idx];
	} while(next_water_id != down_water);

	u64_DynArray_Push(src, temp_idx);

	return 1;
}



// ׷�ٺ������棬��������ͬһ�������ĺӶ�Ҳ���Ϊ���棨���û������������
int32_t* _paint_up_lake_hillslope_new(int32_t* __restrict lake, int32_t lake_num, uint8_t* __restrict dir,
	uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols, int32_t* return_basin_num)
{

	uint64_t idx = 0, upper_idx = 0, down_idx = 0, temp_idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	uint64_t cols64 = (uint64_t)cols;

	// �����ϵ
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	// ջ���������Ӱ���С�ı���
	double frac = 0.001;
	// ��ʼ������ջ
	uint64_t batch_size = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}

	int32_t i = 0, j = 0;
	int32_t lake_value = 0;
	// ȷ�������������ͳ���
	// ��������Ϊ�����ڲ������ۻ������ĵ�
	// ȷ��ÿ�������ĳ���
	// ����������Ԫ����������ڲ���dir=255����˵���ú�����β�̺�
	// ���򣬱��������߽���Ԫ��ȡ�����غ����������ۻ���������ԪΪ�����ĳ�����Ԫ

	// �������������������
	int32_t lakeUpBasinNum = 0;
	int32_t startBasinID = 2 * lake_num;
	int32_t down_water_id = 0;
	uint8_t reverse_fdir = 0, p = 0;

	u64_DynArray* upBasinOutlet = u64_DynArray_Initial(lake_num * 10);

	// ���Һӵ�����
	idx = cols64 + 1;
	for (i = 1; i < rows - 1; i++) {
		for (j = 1; j < cols - 1; j++) {
			lake_value = lake[idx];
			// ����Ǻӵ�
			if ((lake_value == 0) && (upa[idx] > ths)) {
				// �ж��Ƿ��Ǻ���������
				down_idx = _get_down_idx64(dir[idx], idx, cols);
				if ((lake[down_idx] > 0) && (lake[down_idx] <= lake_num)) {
					// ���������㣬�Ƿ�������ͬһ�������ĺӵ���
					if (_check_lake_inlet(idx, lake, re_dir, upa, ths, offset, div)) {
						++lakeUpBasinNum;
						lake[idx] = startBasinID + lakeUpBasinNum;
						u64_DynArray_Push(upBasinOutlet, idx);
					}
				}
			}
			++idx;
		}
		idx += 2;
	}

	uint8_t* lake_type = u8_VLArray_Initial(lake_num + 1, 1);
	uint64_t* lakeOutlet = u64_VLArray_Initial(lake_num + 1, 1);
	float* lakeMaxArea = f32_VLArray_Initial(lake_num + 1, 1);


	// Ѱ�Һ�������
	idx = cols64 + 1;
	for (i = 1; i < rows - 1; i++) {
		for (j = 1; j < cols - 1; j++) {
			lake_value = lake[idx];
			// Ѱ�Һ�����Ԫ
			if ((lake_value > 0) && (lake_value <= lake_num)) {
				// �ж��Ƿ���������
				if (dir[idx] == 255) {
					lake_type[lake_value] = 1;
					lakeMaxArea[lake_value] = upa[idx];
					lakeOutlet[lake_value] = idx;
				}
				if (lake_type[lake_value] == 1) { ; }
				else {
					down_idx = _get_down_idx64(dir[idx], idx, cols);
					// ��������˺�������Ϊ��������
					if (lake[down_idx] != lake_value) {
						if (upa[idx] > lakeMaxArea[lake_value]) {
							lakeMaxArea[lake_value] = upa[idx];
							lakeOutlet[lake_value] = idx;
						}
					}
				}
			}
			++idx;
		}
		idx += 2;
	}

	// Ѱ�Һ�����������·
	for (i = 1; i < lake_num + 1; i++) {
		// �����������β�̺�����ô�ض�������
		if (lake_type[i] != 1) {
			idx = lakeOutlet[i];
			// ���㵱ǰ����������
			// ���ͨ��������������һ����������������·������Ϊһ��������
			do {
				down_idx = _get_down_idx64(dir[idx], idx, cols);
				if (down_idx == 0) {
					break;
				}
				down_water_id = lake[down_idx];
				// �����������һ��ˮ��
				if (down_water_id != 0) {
					// ������������κ��������������򣬲����д���
					// ���ͨ��������·�������κ�������Ϊ������·���������
					if ((down_water_id > 0) && (down_water_id <= lake_num)) {
						++lakeUpBasinNum;
						lake[idx] = startBasinID + lakeUpBasinNum;
						u64_DynArray_Push(upBasinOutlet, idx);

						// ��鵱ǰidx�Ƿ�Ϊ���κ�����outlet
						// ����ǣ������ж����κ�����outlet
						if (idx == lakeOutlet[i]) {
							float max_area = 0.f;
							temp_idx = 0;
							reverse_fdir = re_dir[idx];
							for (p = 0; p < 8; p++) {
								if (reverse_fdir & div[p]) {
									upper_idx = idx + offset[p];
									if ((lake[upper_idx] == i) && (upa[upper_idx] > max_area)) {
										max_area = upa[upper_idx];
										temp_idx = upper_idx;
									}
								}
							}
							lakeOutlet[i] = temp_idx;
						}
					}
					break;
				}
				idx = down_idx;
			} while (1);
		}
	}

	// �������е���ֵ��Ԫ��Ѱ�����������ͺӵ�����
	u64_DynArray* paint_idxs = u64_DynArray_Initial(batch_size);
	i32_DynArray* paint_colors = i32_DynArray_Initial(batch_size);
	idx = cols64 + 1;
	for (i = 1; i < rows - 1; i++) {
		for (j = 1; j < cols - 1; j++) {
			lake_value = lake[idx];
			if (lake_value <= 0) {;}
			else if (lake_value <= lake_num) {
				reverse_fdir = re_dir[idx];
				for (p = 0; p < 8; p++) {
					if (reverse_fdir & div[p]) {
						upper_idx = idx + offset[p];
						if (lake[upper_idx] == 0) {
							u64_DynArray_Push(paint_idxs, upper_idx);
							i32_DynArray_Push(paint_colors, lake_num + lake_value);
						}
					}
				}
			}
			else {
				u64_DynArray_Push(paint_idxs, idx);
				i32_DynArray_Push(paint_colors, lake_value);
			}
			++idx;
		}
		idx += 2;
	}

	int32_t basin_num = lake_num + lakeUpBasinNum;
	int32_t* outlets = i32_VLArray_Initial((basin_num + 1) * 2, 1);
	for (i = 1; i <= lake_num; i++) {
		j = 2 * i;
		outlets[j] = (int32_t)(lakeOutlet[i] / cols64);
		outlets[j + 1] = (int32_t)(lakeOutlet[i] % cols64);
	}
	for (i = 0; i < lakeUpBasinNum; i++) {
		j = 2 * (i + 1 + lake_num);
		outlets[j] = (int32_t)(upBasinOutlet->data[i] / cols64);
		outlets[j + 1] = (int32_t)(upBasinOutlet->data[i] % cols64);
	}
	u64_DynArray_Destroy(upBasinOutlet);

	u64_DynArray* stack = u64_DynArray_Initial(batch_size);
	uint64_t paint_num = paint_idxs->length;
	for (uint64_t probe = 0; probe < paint_num; probe++) {
		_paint_upper_unpainted_int32(paint_idxs->data[probe], paint_colors->data[probe], stack, lake, re_dir, offset, div);
	}

	u64_DynArray_Destroy(stack);
	u64_DynArray_Destroy(paint_idxs);
	i32_DynArray_Destroy(paint_colors);

	free(lake_type);
	free(lakeMaxArea);
	free(lakeOutlet);

	*return_basin_num = basin_num;

	return outlets;
}



int32_t _check_lake_inlet(uint64_t idx, int32_t* __restrict lake, uint8_t* __restrict re_dir, float* __restrict upa, float ths, 
	const int32_t offset[], const uint8_t div[]) {

	int32_t result = 1;
	
	uint8_t reverse_fdir = 0, p = 0;
	uint64_t upper_idx = 0, sub_idx = idx, temp_idx = 0;
	float max_area = 0.f;
	while (1) {
		reverse_fdir = re_dir[sub_idx];
		max_area = 0.f;
		for (p = 0; p < 8; p++) {
			if (reverse_fdir & div[p]) {
				upper_idx = sub_idx + offset[p];
				if (upa[upper_idx] > max_area) {
					max_area = upa[upper_idx];
					temp_idx = upper_idx;
				}
			}
		}
		if (max_area < 1.0f) {	break;	}
		if (lake[temp_idx] > 0) {
			result = 0;
			break;
		}
		sub_idx = temp_idx;
	}
	return result;
}



int32_t _paint_single_lake_catchment(uint8_t* __restrict lake, uint8_t* __restrict re_dir, int32_t rows, int32_t cols,
	int32_t min_row, int32_t min_col, int32_t max_row, int32_t max_col) {

	uint64_t idx = 0;
	uint64_t total_num = rows * (uint64_t)cols;
	uint64_t upper_idx = 0;
	uint8_t reverse_fdir = 0;
	int32_t i = 0, j = 0;
	uint8_t lake_value = 0;
	uint8_t p = 0;

	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// ջ���������Ӱ���С�ı���
	double frac = 0.001;
	uint64_t batch_size = ((uint64_t)(rows * (uint64_t)cols * frac / 10000) + 1) * 10000;
	if (batch_size > 100000000) {
		batch_size = 100000000;
	}
	// ��ʼ������ջ
	u64_DynArray* stack = u64_DynArray_Initial(batch_size);
	uint64_t paint_size = (uint64_t)(max_row - min_row + 1) * (max_col - min_col + 1);
	u64_DynArray* paint_idxs = u64_DynArray_Initial(paint_size);
	u8_DynArray* paint_colors = u8_DynArray_Initial(paint_size);

	// �ҵ���������������
	for (i = min_row; i <= max_row; i++) {
		idx = i * (uint64_t)cols + min_col;
		for (j = min_col; j <= max_col; j++) {
			lake_value = lake[idx];
			if (lake_value > 0) {
				reverse_fdir = re_dir[idx];
				for (p = 0; p < 8; p++) {
					if (reverse_fdir & div[p]) {
						upper_idx = idx + offset[p];
						// ������β��Ǹú�������Ԫ
						if (lake[upper_idx] == 0) {
							u64_DynArray_Push(paint_idxs, upper_idx);
							u8_DynArray_Push(paint_colors, lake_value);
						}
					}
				}
			}
			idx++;
		}
	}

	uint64_t paint_num = paint_idxs->length;
	for (uint64_t probe = 0; probe < paint_num; probe++) {
		_paint_upper_unpainted_uint8(paint_idxs->data[probe], paint_colors->data[probe], stack, lake, re_dir, offset, div);
	}

	u64_DynArray_Destroy(stack);
	u64_DynArray_Destroy(paint_idxs);
	u8_DynArray_Destroy(paint_colors);

	return 1;
}


