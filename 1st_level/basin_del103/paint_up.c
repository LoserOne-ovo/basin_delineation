#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "paint_up.h"

/// <summary>
/// 依据逆d8流向，追溯外流区流域
/// </summary>
/// <param name="ridx"></param>
/// <param name="cidx"></param>
/// <param name="cols"></param>
/// <param name="num"></param>
/// <param name="re_fdir"></param>
/// <param name="basin"></param>
/// <returns></returns>
__declspec(dllexport) int paint_up(unsigned int* ridx, unsigned int* cidx, int cols, 
								   unsigned int num, unsigned char* re_fdir, unsigned short* basin) 
{

	uint64 cols64 = (uint64)cols;
	uint64 idx = 0;
	uint8 reverse_fdir = 0;
	uint16 color;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	cell_quene quene = { 0,0,NULL };
	
	quene.List = (uint64*)calloc(QUENE_SIZE, sizeof(uint64));
	if (quene.List == NULL) {
		fprintf(stderr, "Memory allocation failed!\r\n");
		exit(-1);
	}
	quene.alloc_length = QUENE_SIZE;

	for (uint i = 0; i < num; i++) {

		idx = ridx[i] * cols64 + cidx[i];
		color = basin[idx];
		
		quene.List[0] = idx;
		quene.length = 1;

		while (quene.length > 0) {
			idx = quene.List[quene.length - 1];
			quene.length--;
			basin[idx] = color;
			reverse_fdir = re_fdir[idx];
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					quene_append(&quene, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
			
		}

	}

	free(quene.List);
	quene.List = NULL;
	quene.length = 0;
	quene.alloc_length = 0;

	return 1;
}


int quene_append(cell_quene* src, unsigned long long elem) {

	if (src->length == src->alloc_length) {

		uint newsize = src->alloc_length + QUENE_SIZE;
		uint64* newList = (uint64*)realloc(src->List, newsize * sizeof(uint64));
		if (newList == NULL) {
			fprintf(stderr, "Memory reallocation failed!\r\n");
			exit(-2);
		}
		src->List = newList;
		src->alloc_length = newsize;
	}

	src->List[src->length] = elem;
	src->length++;

	return 1;
}