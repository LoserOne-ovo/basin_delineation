#ifndef _CALC_GC_H
#define _CALC_GC_H

const unsigned int EL_SIZE = 1000;

typedef struct {
	unsigned int length;
	unsigned int alloc_length;
	unsigned long long* List;
}edge_list;

int eL_append(edge_list* src, unsigned long long elem);

#endif

