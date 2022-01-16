#ifndef _LAKES_H_
#define _LAKES_H_




/****************************************
 *   ���ƺ������桢�����������������   *
 ****************************************/

int _paint_up_lake_hillslope_int32(int* lake, int lake_num, unsigned char* re_dir, float* upa, float ths, int rows, int cols);
int _paint_up_lake_hillslope_2_int32(int* lake, int max_lake_id, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols);
int _paint_lake_local_catchment_int32(int* lake, int lake_num, unsigned char* re_dir, int rows, int cols);
int _paint_lake_upper_catchment_int32(int* lake, int lake_id, int* board, unsigned char* re_dir, int rows, int cols);



/**************************************
 *   �޸ĺ�����Χ��ʹ�������������   *
 **************************************/


int _correct_lake_network_int32(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols);
int _update_lake(unsigned long long upper_idx, unsigned long long down_idx, int lake_value, int* basin, unsigned char* re_dir,
	float* upa, float ths, int cols, const unsigned char div[], const int offset[]);

int _correct_lake_network_2_int32(int* lake, unsigned char* dir, unsigned char* re_dir, float* upa, float ths, int rows, int cols);
int _copy_layer_int32(int* src, int* dst, unsigned long long total_num);
int _update_lake_bound_int32(unsigned long long idx, int* water, int* new_layer, unsigned char* dir, int cols, int value);



/*********************
 *	    ��������     *
 *********************/

int* _topology_between_lakes(int* water, int lake_num, int* tag_array, unsigned char* dir, int rows, int cols);
int _find_next_water_body_int32(unsigned long long idx, int* water, unsigned char* dir, int cols);
int _mark_lake_outlet_int32(int* lake, int min_lake_id, int max_lake_id, unsigned char* dir, int rows, int cols);


#endif // !_LAKES_H_
