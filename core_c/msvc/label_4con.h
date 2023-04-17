#ifndef _LABEL_4CON_H_
#define _LABEL_4CON_H_

#include "Array.h"


const int32_t TUPLE_SIZE = 100;
const int32_t EC_SIZE = 100000;

typedef struct {
	int32_t s_cidx;
	int32_t e_cidx;
	int32_t tag_idx;
}con_tuple;

typedef struct {
	int32_t length;
	int32_t alloc_length;
	con_tuple* data;
}tuple_row;

typedef struct {
	int32_t min_tag;
	int32_t max_tag;
}equ_couple;

typedef struct {
	int32_t length;
	int32_t alloc_length;
	equ_couple* data;
}equ_couple_list;


int32_t* _label_4con(uint8_t* __restrict bin_ima, int32_t rows, int32_t cols, int32_t* label_num);
void check_rList_alloc(tuple_row* rList);
int32_t get_tag(tuple_row* rList, int32_t start_idx, int32_t end_idx, equ_couple_list* ecList);
int32_t line_intersection(int32_t a1, int32_t a2, int32_t b1, int32_t b2);
void add_ec(equ_couple_list* ecList, int32_t tag_a, int32_t tag_b);


#endif