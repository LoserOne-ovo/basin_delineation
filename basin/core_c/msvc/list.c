#include <stdlib.h>
#include <stdio.h>
#include "list.h"


int u8_List_append(u8_List* src, unsigned char elem) {

	if (src->length == src->alloc_length) {
		unsigned long long newsize = src->alloc_length + src->batch_size;
		unsigned char* newList = (unsigned char*)realloc(src->List, newsize * sizeof(unsigned char));
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


int u16_List_append(u16_List* src, unsigned short elem) {

	if (src->length == src->alloc_length) {
		unsigned long long newsize = src->alloc_length + src->batch_size;
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


int u32_List_append(u32_List* src, unsigned int elem) {

	if (src->length == src->alloc_length) {
		unsigned long long newsize = src->alloc_length + src->batch_size;
		unsigned int* newList = (unsigned int*)realloc(src->List, newsize * sizeof(unsigned int));
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


int u64_List_append(u64_List* src, unsigned long long elem) {

	if (src->length == src->alloc_length) {
		unsigned long long newsize = src->alloc_length + src->batch_size;
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



int i32_List_append(i32_List* src, int elem) {

	if (src->length == src->alloc_length) {
		unsigned long long newsize = src->alloc_length + src->batch_size;
		unsigned int* newList = (unsigned int*)realloc(src->List, newsize * sizeof(int));
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

	for (unsigned long long i = 0; i < src->length;i++) {
		if (val == src->List[i]) {
			return 1;
		}
	}
	return 0;
}


int check_in_u8_List(unsigned char val, u8_List* src) {

	for (unsigned long long i = 0; i < src->length; i++) {
		if (val == src->List[i]) {
			return 1;
		}
	}
	return 0;
}


int check_in_i32_List(int val, i32_List* src) {

	for (unsigned long long i = 0; i < src->length; i++) {
		if (val == src->List[i]) {
			return 1;
		}
	}
	return 0;
}