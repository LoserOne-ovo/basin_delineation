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

	// ��ʼ�����
	int* __restrict result = (int*)calloc(total_num, sizeof(int));
	if (result == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// ����������
	unsigned char* re_dir = _get_re_dir(dir, rows, cols);


	/* ��ȱ���Ϊÿһ���ӵ����и�ֵ*/

	// ��������
	uint8 reverse_fdir = 0;
	int channel_id = 10001;
	uint8 upper_channel_num = 0;
	uint64 temp_upper_List[8] = { 0 };
	
	// Ԥ��ӶεĹ�ģΪ100000
	int bench_channel_num = 100000;
	// ����ʹ��ջ���ݽṹ
	u64_List streams = { 0,0, bench_channel_num, NULL };
	streams.List = (uint64*)calloc(bench_channel_num, sizeof(unsigned long long));
	if (streams.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// �����������һά����
	idx = (uint64)(outlet_ridx * (uint64)cols + outlet_cidx);
	streams.List[0] = idx;
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
			for (int p = 0; p < 8; p++) {
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
				for (int q = 0; q < upper_channel_num; q++) {
					u64_List_append(&streams, temp_upper_List[q]);
				}
				idx = streams.List[streams.length - 1];
				channel_id++;
			}

			// ���û�����κӵ���Ԫ��˵���Ӷν���
			else {
				streams.length--;
				if (streams.length > 0) {
					idx = streams.List[streams.length - 1];
					channel_id++;
				}
				// ���ջ��û�������ӵ������˳�ѭ��
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

	// ����������
	unsigned char* re_dir = _get_re_dir(dir, rows, cols);

	/* ��ȱ���Ϊÿһ���ӵ����и�ֵ*/

	// ��������
	uint8 reverse_fdir = 0;
	int channel_id = 10000;
	uint8 upper_channel_num = 0;
	uint64 temp_upper_List[8] = { 0 };
	int channel_end_flag = 0;

	// Ԥ��ӶεĹ�ģΪ100000
	int bench_channel_num = 100000;
	// ����ʹ��ջ���ݽṹ
	u64_List streams = { 0,0, bench_channel_num, NULL };
	streams.List = (uint64*)calloc(bench_channel_num, sizeof(unsigned long long));
	if (streams.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}

	// �����������һά����
	idx = (uint64)(outlet_ridx * (uint64)cols + outlet_cidx);
	streams.List[0] = idx;
	streams.length = 1;

	// ���������ڴ��Ļ����ۻ���С����ֵ
	if (upa[idx] <= ths) {
		fprintf(stderr, "Flow accumulation of the outlet is less than the threshold!\r\n");
	}
	
	// ��������
	else {

		while (streams.length > 0) {

			idx = streams.List[--streams.length];
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
					for (int p = 0; p < 8; p++) {
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
							u64_List_append(&streams, upper_idx);
							channel_end_flag = 1;
						}

					}
					// ��������ж���ӵ���Ԫ,�������ǰ�ӶΣ�����ºӶ�
					else if (upper_channel_num > 1) {
						for (uint8 q = 0; q < upper_channel_num; q++) {
							u64_List_append(&streams, temp_upper_List[q]);
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
					for (int p = 0; p < 8; p++) {
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
							u64_List_append(&streams, upper_idx);
							channel_end_flag = 1;
						}

					}
					// ��������ж���ӵ���Ԫ,�������ǰ�ӶΣ�����ºӶ�
					else if (upper_channel_num > 1) {
						for (uint8 q = 0; q < upper_channel_num; q++) {
							u64_List_append(&streams, temp_upper_List[q]);
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

	free(streams.List);
	streams.List = NULL;
	streams.length = 0;
	streams.batch_size = 0;
	streams.alloc_length = 0;

	free(re_dir);
	re_dir = NULL;

	return 1;

}



// ���ƺӵ���ɽ�µ�Ԫ
int _paint_river_hillslope_int32(int* __restrict stream, int min_channel_id, int max_channel_id, unsigned char* __restrict dir, unsigned char* __restrict re_dir, int rows, int cols) {


	/**************************
	 *      ��ʼ������        *
	 **************************/
	
	
	// �������
	int bench_size = 100000;

	// ����
	uint64 total_num = rows * (uint64)cols;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	//const uint8 fdc[8] = { 1,2,4,8,16,32,64,128 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };

	// ��������
	uint64 idx = 0, temp_idx = 0, upper_idx = 0;
	uint8 reverse_fdir = 0, temp_reverse_fdir = 0;
	uint8 cur_dir = 0;
	uint8 upper_channel_num = 0, upper_hs_num = 0;
	int hillslope_id = 0, channel_id = 0;
	uint8 cur_idx = 0;

	// �����б�
	uint64 temp_upper_idx_List[8] = { 0 };
	uint8 temp_upper_dir_List[8] = { 0 };
	uint8 temp_upper_stream_dir_List[8] = { 0 };
	
	// ����ջ
	u64_List stack = { 0,0,bench_size,NULL };
	stack.List = (uint64*)calloc(bench_size, sizeof(unsigned long long));
	if (stack.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}


	/**************************
	 *      ���ƺӵ�����      *
     **************************/


	uint64 count = 0;


	// ѭ������Ӱ��
	for (idx = 0; idx < total_num; idx++) {

		channel_id = stream[idx];


		// ����Ǻӵ���Ԫ
		if (channel_id >= min_channel_id && channel_id <= max_channel_id) {

			count++;
			/*fprintf(stderr, "%llu ", count);*/


			// ���ø�������
			upper_channel_num = upper_hs_num = 0;
			reverse_fdir = re_dir[idx];

			// ���㵱ǰ��Ԫ�����κӵ�����������
			for (int p = 0; p < 8; p++) {
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
				for (int q = 0; q < upper_hs_num; q++) {
					_paint_upper_int32(re_dir, temp_upper_idx_List[q], &stack, hillslope_id, stream, offset, div);
				}
			}
			else {

				// ������뺣�ڣ���һ��������Ԫ����λ����
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
				 *    �жϵ�ǰ��Ԫ�ںӵ��е�λ��    *
				 * **********************************/

				 /* 1.�ӵ�Դͷ */
				if (upper_channel_num == 0) {

					hillslope_id = max_channel_id + (channel_id - min_channel_id) * 3 + 1;
					for (int q = 0; q < upper_hs_num; q++) {
						_paint_upper_int32(re_dir, temp_upper_idx_List[q], &stack, hillslope_id, stream, offset, div);
					}
				}


				/* 2.�ӵ����루ֻ��һ�����Σ�*/
				else if (upper_channel_num == 1) {

					for (int q = 0; q < upper_hs_num; q++) {
						hillslope_id = _decide_hillslope_id(cur_dir, temp_upper_dir_List[q], temp_upper_stream_dir_List,
							upper_channel_num, channel_id, min_channel_id, max_channel_id);
						_paint_upper_int32(re_dir, temp_upper_idx_List[q], &stack, hillslope_id, stream, offset, div);
					}
				}


				/* 2.�ӵ����棨������Σ�*/
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

	// �ͷ���Դ
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

	/* ��Ӧֻ��һ�����κӵ���Ԫ����� */
	if (upper_stream_num == 1) {
		uint8 upper_stream_dir = upper_stream_dir_List[0];

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
// *	ѭ���������ұ���  *
// **********************/
//
//int end_flag = 0; // �������ѭ��ʱ�Ƿ������ӵ�
//int dir_probe = -1, next_dir_probe = -1; // ��¼�����������е�����
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
//// ��˳ʱ�뷽�����ұ���
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
//// ��ʱ�뷽���������
//next_dir_probe = dir_probe - 1;
//if (next_dir_probe < 0) {
//	dir_probe = 7;
//}
//// ��һ������
//while (next_dir_probe != dir_probe) {
//
//	upper_idx = idx + offset[7 - next_dir_probe];
//	// ������������µĽ׶�
//	if (end_flag == 0) {
//
//		// �����ӵ�
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
//	// ���������κӵ�֮��Ĳ��ֻ��鵽������κӵ����ұ���
//	else {
//
//		if (stream[upper_idx] >= min_channel_id) {
//			left_channel_id = stream[upper_idx];
//		}
//		// �����Ǻӵ���Ԫ
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
//	// ������ʱ�뷽�����
//	next_dir_probe = dir_probe - 1;
//	if (next_dir_probe < 0) {
//		dir_probe = 7;
//	}
//}