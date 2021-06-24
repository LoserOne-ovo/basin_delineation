#ifndef _PAINT_UP_H
#define _PAINT_UP_H


const unsigned int QUENE_SIZE = 100000000;


typedef struct {
	unsigned int length;
	unsigned int alloc_length;
	unsigned long long* List;
}cell_quene;


int quene_append(cell_quene* src, unsigned long long elem);


#endif
