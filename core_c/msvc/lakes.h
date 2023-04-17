#ifndef _LAKES_H_
#define _LAKES_H_

#include<stdint.h>


const int32_t DEFAULT_POUR_NUM = 1;
const int32_t DEFAULT_PATH_LENGTH = 10000;


typedef struct {
	uint64_t outlet_idx;
	int32_t upper_water;
	int32_t down_water;
}water_pour;

typedef struct {
	int32_t num;
	water_pour* data;
}lake_pour;


typedef struct {
	int32_t upper_water;
	int32_t down_water;
	u64_DynArray route;
}lake_route;


/****************************************
 *   绘制湖泊坡面、本地流域和完整上游   *
 ****************************************/

int32_t _paint_up_lake_hillslope_int32(int32_t* __restrict lake, int32_t lake_num, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols);
int32_t _paint_up_lake_hillslope_2_int32(int32_t*__restrict lake, int32_t max_lake_id, uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols);
int32_t _paint_lake_local_catchment_int32(int32_t* __restrict lake, int32_t lake_num, uint8_t* __restrict re_dir, int32_t rows, int32_t cols);
int32_t _paint_lake_upper_catchment_int32(int32_t* __restrict lake, int32_t lake_id, int32_t* __restrict board, uint8_t* __restrict re_dir, int32_t rows, int32_t cols);



/**************************************
 *   修改湖泊范围，使其与河网更贴合   *
 **************************************/


int32_t _correct_lake_network_int32(int32_t* __restrict lake, uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols);
int32_t _update_lake(uint64_t upper_idx, uint64_t down_idx, int32_t lake_value, int32_t* __restrict basin, uint8_t* __restrict re_dir,
	float* __restrict upa, float ths, int32_t cols, const uint8_t div[], const int32_t offset[]);

int32_t _correct_lake_network_2_int32(int32_t* __restrict lake, uint8_t* __restrict dir, uint8_t* __restrict re_dir, float* __restrict upa, float ths, int32_t rows, int32_t cols);
int32_t _copy_layer_int32(int32_t* __restrict src, int32_t* __restrict dst, uint64_t total_num);
int32_t _update_lake_bound_int32(uint64_t idx, int32_t* __restrict water, int32_t* __restrict new_layer, uint8_t* __restrict dir, int32_t cols, int32_t value);



/*********************
 *	    湖泊拓扑     *
 *********************/

int32_t* _topology_between_lakes(int32_t* __restrict water, int32_t lake_num, int32_t* __restrict tag_array, uint8_t* __restrict dir, int32_t rows, int32_t cols);
int32_t _find_next_water_body_int32(uint64_t idx, int32_t* __restrict water, uint8_t* __restrict dir, int32_t cols);
uint64_t _find_next_water_body_idx_int32(uint64_t idx, int32_t* __restrict water, uint8_t* __restrict dir, int32_t cols);
int32_t _mark_lake_outlet_int32(int32_t* __restrict lake, int32_t min_lake_id, int32_t max_lake_id, uint8_t* __restrict dir, int32_t rows, int32_t cols);



int32_t _insert_lake_down_water(lake_pour* src, int32_t src_id, int32_t down_id, uint64_t outlet_idx, float* __restrict upa);
int32_t _check_lake_down_existed(lake_pour* src, int32_t down_id);
int32_t _extract_route(u64_DynArray* src, int32_t down_water, uint64_t outlet_idx, int32_t* __restrict lake, uint8_t* __restrict dir, int32_t cols);




int32_t _check_lake_inlet(uint64_t idx, int32_t* __restrict lake, uint8_t* __restrict re_dir, float* __restrict upa, float ths,
	const int32_t offset[], const uint8_t div[]);


#endif // !_LAKES_H_

