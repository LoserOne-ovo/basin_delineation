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

	// ��ʼ�����
	int32_t* __restrict result = (int32_t*)calloc(total_num, sizeof(int32_t));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// ����������
	uint8_t* re_dir = _get_re_dir(dir, rows, cols);


	/* ��ȱ���Ϊÿһ���ӵ����и�ֵ*/

	// ��������
	uint8_t reverse_fdir = 0;
	int32_t channel_id = 10001;
	uint8_t upper_channel_num = 0;
	uint64_t temp_upper_List[8] = { 0 };
	
	// Ԥ��ӶεĹ�ģΪ100000
	int32_t bench_channel_num = 100000;
	// ����ʹ��ջ���ݽṹ
	u64_DynArray streams = { 0,0, bench_channel_num, NULL };
	streams.data = (uint64_t*)calloc(bench_channel_num, sizeof(uint64_t));
	if (streams.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// �����������һά����
	idx = (uint64_t)(outlet_ridx * (uint64_t)cols + outlet_cidx);
	streams.data[0] = idx;
	streams.length = 1;
	
	// ���������ڴ��Ļ����ۻ���С����ֵ
	if (upa[idx] <= ths) {
		fprintf(stderr, "Flow accumulation of the outlet is less than the threshold!\r\n");
	}
	// ��������
	else {

		// ��ѭ����ʹ��break����ѭ������ʡ�Ƚϴ���
		while (1) {

			// ���ӵ���Ԫ��ֵ
			result[idx] = channel_id;
			// ��ȡ������
			reverse_fdir = re_dir[idx];
			// �������κӵ�����
			upper_channel_num = 0;

			// ����������Ԫ��Ѱ�Һӵ�
			for (int32_t p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					// ����������Ԫһά����
					reverse_fdir -= div[p];
					upper_idx = idx + offset[p];
					// ���������Ԫ��һ���ӵ������¼����Ԫ
					if (upa[upper_idx] > ths) {
						temp_upper_List[upper_channel_num++] = upper_idx;
					}
				}
			}

			// ���ֻ��һ�����κӵ���Ԫ��˵��������ͬһ���Ӷ�
			if (upper_channel_num == 1) {
				idx = temp_upper_List[0];
			}

			// ����ж���ӵ���Ԫ��˵�����ںӵ����洦��������ǰ�ӶΣ�������µĺӶ�
			else if (upper_channel_num > 1) {
				streams.length--;
				for (int32_t q = 0; q < upper_channel_num; q++) {
					u64_DynArray_Push(&streams, temp_upper_List[q]);
				}
				idx = streams.data[streams.length - 1];
				channel_id++;
			}

			// ���û�����κӵ���Ԫ��˵���Ӷν���
			else {
				streams.length--;
				if (streams.length > 0) {
					idx = streams.data[streams.length - 1];
					channel_id++;
				}
				// ���ջ��û�������ӵ������˳�ѭ��
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

	// ����������
	uint8_t* re_dir = _get_re_dir(dir, rows, cols);

	/* ��ȱ���Ϊÿһ���ӵ����и�ֵ*/

	// ��������
	uint8_t reverse_fdir = 0;
	int32_t channel_id = 10000;
	uint8_t upper_channel_num = 0;
	uint64_t temp_upper_List[8] = { 0 };
	int32_t channel_end_flag = 0;

	// Ԥ��ӶεĹ�ģΪ100000
	int32_t bench_channel_num = 100000;
	// ����ʹ��ջ���ݽṹ
	u64_DynArray streams = { 0,0, bench_channel_num, NULL };
	streams.data = (uint64_t*)calloc(bench_channel_num, sizeof(uint64_t));
	if (streams.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// �����������һά����
	idx = (uint64_t)(outlet_ridx * (uint64_t)cols + outlet_cidx);
	streams.data[0] = idx;
	streams.length = 1;

	// ���������ڴ��Ļ����ۻ���С����ֵ
	if (upa[idx] <= ths) {
		fprintf(stderr, "Flow accumulation of the outlet is less than the threshold!\r\n");
	}
	
	// ��������
	else {

		while (streams.length > 0) {

			idx = streams.data[--streams.length];
			channel_end_flag = 0;

			// ����Ӷε���ʼ�ں�����
			if (lake[idx] == 1) {

				channel_id++;
				while (channel_end_flag == 0) {

					lake[idx] = channel_id;
					// ��ȡ������
					reverse_fdir = re_dir[idx];
					// �������κӵ�����
					upper_channel_num = 0;

					// ����������Ԫ��Ѱ�Һӵ�
					for (int32_t p = 0; p < 8; p++) {
						if (reverse_fdir >= div[p]) {
							// ����������Ԫһά����
							reverse_fdir -= div[p];
							upper_idx = idx + offset[p];
							// ���������Ԫ��һ���ӵ������¼����Ԫ
							if (upa[upper_idx] > ths) {
								temp_upper_List[upper_channel_num++] = upper_idx;
							}
						}
					}

					// ���ֻ������ֻ��һ���Ӷ���Ԫ
					if (upper_channel_num == 1) {
						upper_idx = temp_upper_List[0];
						// ������κӵ���ԪҲλ�ں����⣬�������µĺӶ�
						if (lake[upper_idx] == 1) {
							idx = upper_idx;
						}
						// ������κӵ���Ԫλ�ں����ڣ�������ǰ�ӶΣ������µĺӶ�
						else {
							u64_DynArray_Push(&streams, upper_idx);
							channel_end_flag = 1;
						}

					}
					// ��������ж���ӵ���Ԫ,�������ǰ�ӶΣ�����ºӶ�
					else if (upper_channel_num > 1) {
						for (uint8_t q = 0; q < upper_channel_num; q++) {
							u64_DynArray_Push(&streams, temp_upper_List[q]);
						}
						channel_end_flag = 1;
					}
					// �������û�кӵ���Ԫ���������ǰ�Ӷ�
					else {
						channel_end_flag = 1;
					}
				} // ����������ĳһ���Ӷε�׷��
			}

			// ����Ӷε���ʼ�ں�����
			else {

				while (channel_end_flag == 0) {

					// ��ȡ������
					reverse_fdir = re_dir[idx];
					// �������κӵ�����
					upper_channel_num = 0;

					// ����������Ԫ��Ѱ�Һӵ�
					for (int32_t p = 0; p < 8; p++) {
						if (reverse_fdir >= div[p]) {
							// ����������Ԫһά����
							reverse_fdir -= div[p];
							upper_idx = idx + offset[p];
							// ���������Ԫ��һ���ӵ������¼����Ԫ
							if (upa[upper_idx] > ths) {
								temp_upper_List[upper_channel_num++] = upper_idx;
							}
						}
					}

					// ���ֻ������ֻ��һ���Ӷ���Ԫ
					if (upper_channel_num == 1) {
						// ������κӵ���ԪҲλ�ں����ڣ��������µĺӶ�
						upper_idx = temp_upper_List[0];
						if (lake[upper_idx] > 1) {
							idx = upper_idx;
						}
						// ������κӵ���Ԫλ�ں����⣬�����µĺӶ�
						else {
							u64_DynArray_Push(&streams, upper_idx);
							channel_end_flag = 1;
						}

					}
					// ��������ж���ӵ���Ԫ,�������ǰ�ӶΣ�����ºӶ�
					else if (upper_channel_num > 1) {
						for (uint8_t q = 0; q < upper_channel_num; q++) {
							u64_DynArray_Push(&streams, temp_upper_List[q]);
						}
						channel_end_flag = 1;
					}
					// �������û�кӵ���Ԫ���������ǰ�Ӷ�
					else {
						channel_end_flag = 1;
					}

				} // ����������ĳһ���Ӷε�׷��

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



// ���ƺӵ���ɽ�µ�Ԫ
int32_t _paint_river_hillslope_int32(int32_t* __restrict stream, int32_t min_channel_id, int32_t max_channel_id, uint8_t* __restrict dir, uint8_t* __restrict re_dir, int32_t rows, int32_t cols) {


	/**************************
	 *      ��ʼ������        *
	 **************************/
	
	
	// �������
	int32_t bench_size = 100000;

	// ����
	uint64_t total_num = rows * (uint64_t)cols;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	//const uint8_t fdc[8] = { 1,2,4,8,16,32,64,128 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// ��������
	uint64_t idx = 0, temp_idx = 0, upper_idx = 0;
	uint8_t reverse_fdir = 0, temp_reverse_fdir = 0;
	uint8_t cur_dir = 0;
	uint8_t upper_channel_num = 0, upper_hs_num = 0;
	int32_t hillslope_id = 0, channel_id = 0;
	uint8_t cur_idx = 0;

	// �����б�
	uint64_t temp_upper_idx_List[8] = { 0 };
	uint8_t temp_upper_dir_List[8] = { 0 };
	uint8_t temp_upper_stream_dir_List[8] = { 0 };
	
	// ����ջ
	u64_DynArray stack = { 0,0,bench_size,NULL };
	stack.data = (uint64_t*)calloc(bench_size, sizeof(uint64_t));
	if (stack.data == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}


	/**************************
	 *      ���ƺӵ�����      *
     **************************/


	uint64_t count = 0;


	// ѭ������Ӱ��
	for (idx = 0; idx < total_num; idx++) {

		channel_id = stream[idx];


		// ����Ǻӵ���Ԫ
		if (channel_id >= min_channel_id && channel_id <= max_channel_id) {

			count++;


			// ���ø�������
			upper_channel_num = upper_hs_num = 0;
			reverse_fdir = re_dir[idx];

			// ���㵱ǰ��Ԫ�����κӵ�����������
			for (int32_t p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					reverse_fdir -= div[p];
					upper_idx = idx + offset[p];
					// ���������Ԫ��һ���ӵ������¼����Ԫ
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

			// ������������յ�,��ʱ����Դͷ�´���
			if (cur_dir == 255) {
				hillslope_id = max_channel_id + (channel_id - min_channel_id) * 3 + 1;
				for (int32_t q = 0; q < upper_hs_num; q++) {
					_paint_upper_int32(temp_upper_idx_List[q], hillslope_id, &stack, stream, re_dir, offset, div);
				}
			}
			else {

				// ������뺣�ڣ���һ��������Ԫ����λ����
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
				 *    �жϵ�ǰ��Ԫ�ںӵ��е�λ��    *
				 * **********************************/

				 /* 1.�ӵ�Դͷ */
				if (upper_channel_num == 0) {

					hillslope_id = max_channel_id + (channel_id - min_channel_id) * 3 + 1;
					for (int32_t q = 0; q < upper_hs_num; q++) {
						_paint_upper_int32(temp_upper_idx_List[q], hillslope_id, &stack, stream, re_dir, offset, div);
					}
				}


				/* 2.�ӵ����루ֻ��һ�����Σ�*/
				else if (upper_channel_num == 1) {

					for (int32_t q = 0; q < upper_hs_num; q++) {
						hillslope_id = _decide_hillslope_id(cur_dir, temp_upper_dir_List[q], temp_upper_stream_dir_List,
							upper_channel_num, channel_id, min_channel_id, max_channel_id);
						_paint_upper_int32(temp_upper_idx_List[q], hillslope_id, &stack, stream, re_dir, offset, div);
					}
				}


				/* 2.�ӵ����棨������Σ�*/
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

	// �ͷ���Դ
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

	/* ��Ӧֻ��һ�����κӵ���Ԫ����� */
	if (upper_stream_num == 1) {
		uint8_t upper_stream_dir = upper_stream_dir_List[0];

		// ˳ʱ�뷽��û����Ȧ
		// ����˳ʱ�뷽��Ѱ���ұ���
		if (cur_dir < upper_stream_dir) {
			if (hs_dir > cur_dir && hs_dir < upper_stream_dir) {
				return max_stream_id + (stream_id - min_stream_id) * 3 + 2; // �ұ���
			}
			else {
				return max_stream_id + (stream_id - min_stream_id) * 3 + 3; // �����
			}
		}
		// ��ʱ�뷽��û����Ȧ
		// ������ʱ�뷽��Ѱ�������
		else {
			if (hs_dir < cur_dir && hs_dir > upper_stream_dir) {
				return max_stream_id + (stream_id - min_stream_id) * 3 + 3; // �����
			}
			else {
				return max_stream_id + (stream_id - min_stream_id) * 3 + 2; // �ұ���
			}
		}
	}

	/* ��Ӧ�ж�����κӵ���Ԫ����� */
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
			return max_stream_id + (stream_id - min_stream_id) * 3 + 2; // �ұ���
		}
		else if (encounter_channel_num == upper_stream_num) {
			return max_stream_id + (stream_id - min_stream_id) * 3 + 3; // �����
		}
		else {
			return max_stream_id + (stream_id - min_stream_id) * 3 + 1; // �ݶ�Ϊͷ��
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
 *      �������ڲ��������ұ��º�Դͷ��      *
 ********************************************/
int32_t _delineate_basin_hillslope(uint8_t* __restrict stream, uint8_t* __restrict dir, 
	int32_t rows, int32_t cols, uint8_t nodata) {


	/**************************
	 *      ��ʼ������        *
	 **************************/

	 // �������
	int32_t bench_size = 100000;

	// ����
	uint64_t total_num = rows * (uint64_t)cols;
	const uint8_t div[8] = { 128,64,32,16,8,4,2,1 };
	//const uint8_t fdc[8] = { 1,2,4,8,16,32,64,128 };
	const int32_t offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// ��������
	uint64_t idx = 0, temp_idx = 0, upper_idx = 0;
	uint8_t reverse_fdir = 0, temp_reverse_fdir = 0;
	uint8_t cur_dir = 0, hs_dir = 0, upper_stream_dir = 0;
	uint8_t upper_channel_num = 0, upper_hs_num = 0;
	uint8_t hillslope_id = 0;
	uint8_t head_slope_flag = 0;
	uint8_t p = 0, q = 0;

	// �����б�
	uint64_t temp_upper_idx_List[8] = { 0 };
	uint8_t temp_upper_dir_List[8] = { 0 };
	uint8_t temp_upper_stream_dir_List[8] = { 0 };

	// ����ջ
	u64_DynArray* stack = u64_DynArray_Initial(bench_size);
	
	// �������������
	uint8_t* re_dir = _get_re_dir(dir, rows, cols);

	/********************************************
	 *      �������ڲ��������ұ��º�Դͷ��      *
	 ********************************************/

	// ѭ������Ӱ��
	for (idx = 0; idx < total_num; idx++) {
		// �����ǰ��Ԫ�Ǻӵ���Ԫ
		if (stream[idx] == 1) {

			// ���ø�������
			upper_channel_num = upper_hs_num = 0;
			reverse_fdir = re_dir[idx];
			cur_dir = dir[idx];

			// ���㵱ǰ��Ԫ�����κӵ���Ԫ������������Ԫ����
			for (p = 0; p < 8; p++) {
				if (reverse_fdir & div[p]) {
					upper_idx = idx + offset[p];
					// ���������Ԫ��һ���ӵ������¼����Ԫ
					if (stream[upper_idx] == 1) {
						temp_upper_stream_dir_List[upper_channel_num++] = div[p];
					}
					else {
						temp_upper_dir_List[upper_hs_num] = div[p];
						temp_upper_idx_List[upper_hs_num++] = upper_idx;
					}
				}
			}
			
			// �жϵ�Ԫ��Ԫ�Ƿ���Դͷ�º���Ԫ
			// 8����Χ����nodataֵ���϶�Ϊ��Դͷ������Դͷ��
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


			// ������뺣�ڣ���һ��������Ԫ����λ����
			if (cur_dir == 0) {
				for (p = 0; p < 8; p++) {
					temp_idx = idx + offset[p];
					if (dir[temp_idx] == nodata) {
						cur_dir = div[p];
						break;
					}
				}
			}

			// ����Դͷ��
			// ������������յ�,��ʱ����Դͷ�´���
			if ((head_slope_flag == 1) || (cur_dir == 255)) {
				for (q = 0; q < upper_hs_num; q++) {
					hillslope_id = 4;
					_paint_upper_uint8(temp_upper_idx_List[q], hillslope_id, stack, stream, re_dir, offset, div);
				}
			}
			// ���򣬻������ұ���
			else {
				// ������������
				for (q = 0; q < upper_hs_num; q++) {
					hs_dir = temp_upper_dir_List[q];
					hillslope_id = _dertermine_hillslope_postition(cur_dir, hs_dir, upper_stream_dir);
					_paint_upper_uint8(temp_upper_idx_List[q], hillslope_id, stack, stream, re_dir, offset, div);
				}
			}
		}
	}

	// �ͷ���Դ
	free(re_dir);
	re_dir = NULL;
	u64_DynArray_Destroy(stack);
	stack = NULL;

	return 1;
}


uint8_t _dertermine_hillslope_postition(uint8_t cur_dir, uint8_t hs_dir, uint8_t upper_stream_dir) {

	// ˳ʱ�뷽��û����Ȧ
	// ����˳ʱ�뷽��Ѱ���ұ���
	if (cur_dir < upper_stream_dir) {
		if (hs_dir > cur_dir && hs_dir < upper_stream_dir) {
			return 2; // �ұ���
		}
		else {
			return 3; // �����
		}
	}
	// ��ʱ�뷽��û����Ȧ
	// ������ʱ�뷽��Ѱ�������
	else {
		if (hs_dir < cur_dir && hs_dir > upper_stream_dir) {
			return 3; // �����
		}
		else {
			return 2; // �ұ���
		}
	}

}


