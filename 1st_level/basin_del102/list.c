#include <stdlib.h>
#include <stdio.h>
#include "list.h"


int u16_List_append(u16_List* src, unsigned short elem, unsigned int d_size) {

	if (src->length == src->alloc_length) {

		unsigned int newsize = src->alloc_length + d_size;
		unsigned short* newList = (unsigned short*)realloc(src->List, newsize * sizeof(unsigned short));
		if (newList == NULL) {
			fprintf(stderr, "Memory reallocation failed in line %d of list.c \r\n", __LINE__);
			exit(-1);
		}
		src->List = newList;
		src->alloc_length = newsize;
	}

	src->List[src->length] = elem;
	src->length++;

	return 1;
}


int u64_List_append(u64_List* src, unsigned long long elem, unsigned int d_size) {

	if (src->length == src->alloc_length) {

		unsigned int newsize = src->alloc_length + d_size;
		unsigned long long* newList = (unsigned long long*)realloc(src->List, newsize * sizeof(unsigned long long));
		if (newList == NULL) {
			fprintf(stderr, "Memory reallocation failed in line %d of list.c \r\n", __LINE__);
			exit(-1);
		}
		src->List = newList;
		src->alloc_length = newsize;
	}

	src->List[src->length] = elem;
	src->length++;

	return 1;
}


int check_in_u16_List(unsigned short val, u16_List* src) {

	for (unsigned int i = 0; i < src->length;i++) {
		if (val == src->List[i]) {
			return 1;
		}
	}
	return 0;
}
