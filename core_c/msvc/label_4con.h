#ifndef _LABEL_4CON_H_
#define _LABEL_4CON_H_

const int TUPLE_SIZE = 100;
const int EC_SIZE = 100000;

typedef struct {
	unsigned int s_cidx;
	unsigned int e_cidx;
	unsigned int tag_idx;
}con_tuple;

typedef struct {
	unsigned int length;
	unsigned int alloc_length;
	con_tuple* List;
}tuple_row;

typedef struct {

	unsigned int min_tag;
	unsigned int max_tag;

}equ_couple;

typedef struct {
	unsigned int length;
	unsigned int alloc_length;
	equ_couple* List;
}equ_couple_list;


unsigned int* _label_4con(unsigned char* __restrict bin_ima, int rows, int cols, unsigned int* label_num);
void check_rList_alloc(tuple_row* rList);
unsigned int get_tag(tuple_row* rList, unsigned int start_idx, unsigned int end_idx, equ_couple_list* ecList);
int line_intersection(unsigned int a1, unsigned int a2, unsigned int b1, unsigned int b2);
void add_ec(equ_couple_list* ecList, unsigned int tag_a, unsigned int tag_b);
unsigned int min_uint(unsigned int a, unsigned int b);
unsigned int max_uint(unsigned int a, unsigned int b);

#endif