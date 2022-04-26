#ifndef _LAKES_H_
#define _LAKES_H_


const int DEFAULT_POUR_NUM = 1;
const int DEFAULT_PATH_LENGTH = 10000;



typedef struct {
	unsigned long long outlet_idx;
	int upper_water;
	int down_water;
}water_pour;

typedef struct {
	int num;
	water_pour* List;
}lake_pour;


typedef struct {
	int upper_water;
	int down_water;
	u64_List route;
}lake_route;



/****************************************
 *   绘制湖泊坡面、本地流域和完整上游   *
 ****************************************/

int _paint_up_lake_hillslope_int32(int* __restrict lake, int lake_num, unsigned char* __restrict re_dir, float* __restrict upa, float ths, int rows, int cols);
int _paint_up_lake_hillslope_2_int32(int*__restrict lake, int max_lake_id, unsigned char* __restrict dir, unsigned char* __restrict re_dir, float* __restrict upa, float ths, int rows, int cols);
int _paint_lake_local_catchment_int32(int* __restrict lake, int lake_num, unsigned char* __restrict re_dir, int rows, int cols);
int _paint_lake_upper_catchment_int32(int* __restrict lake, int lake_id, int* __restrict board, unsigned char* __restrict re_dir, int rows, int cols);



/**************************************
 *   修改湖泊范围，使其与河网更贴合   *
 **************************************/


int _correct_lake_network_int32(int* __restrict lake, unsigned char* __restrict dir, unsigned char* __restrict re_dir, float* __restrict upa, float ths, int rows, int cols);
int _update_lake(unsigned long long upper_idx, unsigned long long down_idx, int lake_value, int* __restrict basin, unsigned char* __restrict re_dir,
	float* __restrict upa, float ths, int cols, const unsigned char div[], const int offset[]);

int _correct_lake_network_2_int32(int* __restrict lake, unsigned char* __restrict dir, unsigned char* __restrict re_dir, float* __restrict upa, float ths, int rows, int cols);
int _copy_layer_int32(int* __restrict src, int* __restrict dst, unsigned long long total_num);
int _update_lake_bound_int32(unsigned long long idx, int* __restrict water, int* __restrict new_layer, unsigned char* __restrict dir, int cols, int value);



/*********************
 *	    湖泊拓扑     *
 *********************/

int* _topology_between_lakes(int* __restrict water, int lake_num, int* __restrict tag_array, unsigned char* __restrict dir, int rows, int cols);
int _find_next_water_body_int32(unsigned long long idx, int* __restrict water, unsigned char* __restrict dir, int cols);
int _mark_lake_outlet_int32(int* __restrict lake, int min_lake_id, int max_lake_id, unsigned char* __restrict dir, int rows, int cols);



int _insert_lake_down_water(lake_pour* src, int src_id, int down_id, unsigned long long outlet_idx, float* __restrict upa);
int _check_lake_down_existed(lake_pour* src, int down_id);
int _extract_route(u64_List* src, int down_water, unsigned long long outlet_idx, int* __restrict lake, unsigned char* __restrict dir, int cols);


#endif // !_LAKES_H_

