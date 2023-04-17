#include <stdlib.h>
#include <stdio.h>
#include "Array.h"


u8_DynArray* u8_DynArray_Initial(uint64_t length) {

	u8_DynArray* p = (u8_DynArray*)malloc(sizeof(u8_DynArray));
	if (p == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of uint8 dynamic array.\r\n");
		exit(-1);
	}
	p->length = 0;
	p->batch_size = length;

	p->data = (uint8_t*)malloc(length * sizeof(uint8_t));
	if (p->data == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of uint8 dynamic array.\r\n");
		exit(-1);
	}
	p->alloc_length = length;

	return p;
}

u16_DynArray* u16_DynArray_Initial(uint64_t length) {

	u16_DynArray* p = (u16_DynArray*)malloc(sizeof(u16_DynArray));
	if (p == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of uint16 dynamic array.\r\n");
		exit(-1);
	}
	p->length = 0;
	p->batch_size = length;

	p->data = (uint16_t*)malloc(length * sizeof(uint16_t));
	if (p->data == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of uint16 dynamic array.\r\n");
		exit(-1);
	}
	p->alloc_length = length;

	return p;
}

u32_DynArray* u32_DynArray_Initial(uint64_t length) {

	u32_DynArray* p = (u32_DynArray*)malloc(sizeof(u32_DynArray));
	if (p == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of uint32 dynamic array.\r\n");
		exit(-1);
	}
	p->length = 0;
	p->batch_size = length;

	p->data = (uint32_t*)malloc(length * sizeof(uint32_t));
	if (p->data == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of uint32 dynamic array.\r\n");
		exit(-1);
	}
	p->alloc_length = length;

	return p;
}

u64_DynArray* u64_DynArray_Initial(uint64_t length) {

	u64_DynArray* p = (u64_DynArray*)malloc(sizeof(u64_DynArray));
	if (p == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of uint64 dynamic array.\r\n");
		exit(-1);
	}
	p->length = 0;
	p->batch_size = length;

	p->data = (uint64_t*)malloc(length * sizeof(uint64_t));
	if (p->data == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of uint64 dynamic array.\r\n");
		exit(-1);
	}
	p->alloc_length = length;

	return p;
}

i32_DynArray* i32_DynArray_Initial(uint64_t length) {

	i32_DynArray* p = (i32_DynArray*)malloc(sizeof(i32_DynArray));
	if (p == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of int32 dynamic array.\r\n");
		exit(-1);
	}
	p->length = 0;
	p->batch_size = length;

	p->data = (int32_t*)malloc(length * sizeof(int32_t));
	if (p->data == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of int32 dynamic array.\r\n");
		exit(-1);
	}
	p->alloc_length = length;

	return p;
}




void u8_DynArray_Destroy(u8_DynArray* p) {
	free(p->data);
	free(p);
	p = NULL;
}

void u16_DynArray_Destroy(u16_DynArray* p) {
	free(p->data);
	free(p);
	p = NULL;
}

void u32_DynArray_Destroy(u32_DynArray* p) {
	free(p->data);
	free(p);
	p = NULL;
}

void u64_DynArray_Destroy(u64_DynArray* p) {
	free(p->data);
	free(p);
	p = NULL;
}

void i32_DynArray_Destroy(i32_DynArray* p) {
	free(p->data);
	free(p);
	p = NULL;
}




int32_t u8_DynArray_Push(u8_DynArray* src, uint8_t elem) {

	if (src->length == src->alloc_length) {
		uint64_t newsize = src->alloc_length + src->batch_size;
		uint8_t* newList = (uint8_t*)realloc(src->data, newsize * sizeof(uint8_t));
		if (newList == NULL) {
			fprintf(stderr, "memory reallocation failed in uint8 dynamic array.\r\n");
			exit(-1);
		}
		src->data = newList;
		src->alloc_length = newsize;
	}
	src->data[src->length] = elem;
	src->length++;

	return 1;
}

int32_t u16_DynArray_Push(u16_DynArray* src, uint16_t elem) {

	if (src->length == src->alloc_length) {
		uint64_t newsize = src->alloc_length + src->batch_size;
		uint16_t* newList = (uint16_t*)realloc(src->data, newsize * sizeof(uint16_t));
		if (newList == NULL) {
			fprintf(stderr, "memory reallocation failed in uint16 dynamic array.\r\n");
			exit(-1);
		}
		src->data = newList;
		src->alloc_length = newsize;
	}
	src->data[src->length] = elem;
	src->length++;

	return 1;
}

int32_t u32_DynArray_Push(u32_DynArray* src, uint32_t elem) {

	if (src->length == src->alloc_length) {
		uint64_t newsize = src->alloc_length + src->batch_size;
		uint32_t* newList = (uint32_t*)realloc(src->data, newsize * sizeof(uint32_t));
		if (newList == NULL) {
			fprintf(stderr, "memory reallocation failed in uint32 dynamic array.\r\n");
			exit(-1);
		}
		src->data = newList;
		src->alloc_length = newsize;
	}
	src->data[src->length] = elem;
	src->length++;

	return 1;
}

int32_t u64_DynArray_Push(u64_DynArray* src, uint64_t elem) {

	if (src->length == src->alloc_length) {
		uint64_t newsize = src->alloc_length + src->batch_size;
		uint64_t* newList = (uint64_t*)realloc(src->data, newsize * sizeof(uint64_t));
		if (newList == NULL) {
			fprintf(stderr, "memory reallocation failed in uint64 dynamic array.\r\n");
			exit(-1);
		}
		src->data = newList;
		src->alloc_length = newsize;
	}
	src->data[src->length] = elem;
	src->length++;

	return 1;
}

int32_t i32_DynArray_Push(i32_DynArray* src, int32_t elem) {

	if (src->length == src->alloc_length) {
		uint64_t newsize = src->alloc_length + src->batch_size;
		uint32_t* newList = (uint32_t*)realloc(src->data, newsize * sizeof(int32_t));
		if (newList == NULL) {
			fprintf(stderr, "memory reallocation failed in uint8 dynamic array.\r\n");
			exit(-1);
		}
		src->data = newList;
		src->alloc_length = newsize;
	}
	src->data[src->length] = elem;
	src->length++;

	return 1;
}




int32_t check_in_u8_DynArray(uint8_t val, u8_DynArray* src) {

	for (uint64_t i = 0; i < src->length; i++) {
		if (val == src->data[i]) {
			return 1;
		}
	}
	return 0;
}

int32_t check_in_u16_DynArray(uint16_t val, u16_DynArray* src) {

	for (uint64_t i = 0; i < src->length;i++) {
		if (val == src->data[i]) {
			return 1;
		}
	}
	return 0;
}

int32_t check_in_u32_DynArray(uint32_t val, u32_DynArray* src) {

	for (uint64_t i = 0; i < src->length; i++) {
		if (val == src->data[i]) {
			return 1;
		}
	}
	return 0;
}

int32_t check_in_u64_DynArray(uint64_t val, u64_DynArray* src) {

	for (uint64_t i = 0; i < src->length; i++) {
		if (val == src->data[i]) {
			return 1;
		}
	}
	return 0;
}

int32_t check_in_i32_DynArray(int32_t val, i32_DynArray* src) {

	for (uint64_t i = 0; i < src->length; i++) {
		if (val == src->data[i]) {
			return 1;
		}
	}
	return 0;
}



uint8_t** u8_VLArray2D_Initial(uint64_t m, uint64_t n, int32_t flag) {

	if (m <= 0 || n <= 0) {
		fprintf(stderr, "memory allocation failed(0) in initialization of uint8 2D array.\r\n");
		exit(-1);
	}

	uint8_t** p = (uint8_t**)malloc(m * sizeof(uint8_t*));
	if (p == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of uint8 2D array.\r\n");
		exit(-1);
	}
	if (flag == 0) {
		for (uint64_t i = 0; i < m; i++) {
			p[i] = (uint8_t*)malloc(n * sizeof(uint8_t));
			if (p[i] == NULL) {
				fprintf(stderr, "memory allocation failed in initialization of uint8_t 2D array.\r\n");
				exit(-1);
			}
		}
	}
	else {
		for (uint64_t i = 0; i < m; i++) {
			p[i] = (uint8_t*)calloc(n, sizeof(uint8_t));
			if (p[i] == NULL) {
				fprintf(stderr, "memory allocation failed in initialization of uint8_t 2D array.\r\n");
				exit(-1);
			}
		}
	}

	return p;
}

int32_t** i32_VLArray2D_Initial(uint64_t m, uint64_t n, int32_t flag) {

	if (m <= 0 || n <= 0) {
		fprintf(stderr, "memory allocation failed(0) in initialization of int32 2D array.\r\n");
		exit(-1);
	}


	int32_t** p = (int32_t**)malloc(m * sizeof(int32_t*));
	if (p == NULL) {
		fprintf(stderr, "memory allocation failed in initialization of int32 2D array.\r\n");
		exit(-1);
	}
	if (flag == 0) {
		for (uint64_t i = 0; i < m; i++) {
			p[i] = (int32_t*)malloc(n * sizeof(int32_t));
			if (p[i] == NULL) {
				fprintf(stderr, "memory allocation failed in initialization of int32 2D array.\r\n");
				exit(-1);
			}
		}
	}
	else {
		for (uint64_t i = 0; i < m; i++) {
			p[i] = (int32_t*)calloc(n, sizeof(int32_t));
			if (p[i] == NULL) {
				fprintf(stderr, "memory allocation failed in initialization of int32 2D array.\r\n");
				exit(-1);
			}
		}
	}

	return p;
}


uint8_t* u8_VLArray_Initial(uint64_t m, int32_t flag) {

	if (m <= 0) {
		fprintf(stderr, "memory allocation failed(0) in initialization of uint8 array.\r\n");
		exit(-1);
	}

	uint8_t* p;
	if (flag == 0) {
		p = (uint8_t*)malloc(m * sizeof(uint8_t));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of uint8 array.\r\n");
			exit(-1);
		}
	}
	else {
		p = (uint8_t*)calloc(m, sizeof(uint8_t));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of uint8 array.\r\n");
			exit(-1);
		}
	}
	return p;
}

uint16_t* u16_VLArray_Initial(uint64_t m, int32_t flag) {

	if (m <= 0) {
		fprintf(stderr, "memory allocation failed(0) in initialization of uint16 array.\r\n");
		exit(-1);
	}

	uint16_t* p;
	if (flag == 0) {
		p = (uint16_t*)malloc(m * sizeof(uint16_t));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of uint16 array.\r\n");
			exit(-1);
		}
	}
	else {
		p = (uint16_t*)calloc(m, sizeof(uint16_t));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of uint16 array.\r\n");
			exit(-1);
		}
	}
	return p;
}

int32_t* i32_VLArray_Initial(uint64_t m, int32_t flag) {

	if (m <= 0) {
		fprintf(stderr, "memory allocation failed(0) in initialization of int32 array.\r\n");
		exit(-1);
	}

	int32_t* p;
	if (flag == 0) {
		p = (int32_t*)malloc(m * sizeof(int32_t));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of int32 array.\r\n");
			exit(-1);
		}
	}
	else {
		p = (int32_t*)calloc(m, sizeof(int32_t));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of int32 array.\r\n");
			exit(-1);
		}
	}
	return p;
}


uint64_t* u64_VLArray_Initial(uint64_t m, int32_t flag) {

	if (m <= 0) {
		fprintf(stderr, "memory allocation failed(0) in initialization of uint64 array.\r\n");
		exit(-1);
	}

	uint64_t* p;
	if (flag == 0) {
		p = (uint64_t*)malloc(m * sizeof(uint64_t));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of uint64 array.\r\n");
			exit(-1);
		}
	}
	else {
		p = (uint64_t*)calloc(m, sizeof(uint64_t));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of uint64 array.\r\n");
			exit(-1);
		}
	}
	return p;
}


float* f32_VLArray_Initial(uint64_t m, int32_t flag) {
	
	if (m <= 0) {
		fprintf(stderr, "memory allocation failed(0) in initialization of float32 array.\r\n");
		exit(-1);
	}

	float* p;
	if (flag == 0) {
		p = (float*)malloc(m * sizeof(float));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of float32 array.\r\n");
			exit(-1);
		}
	}
	else {
		p = (float*)calloc(m, sizeof(float));
		if (p == NULL) {
			fprintf(stderr, "memory allocation failed in initialization of float32 array.\r\n");
			exit(-1);
		}
	}
	return p;
}






void u8_VLArray2D_Destroy(uint8_t** p, uint64_t m) {
	for (uint64_t i = 0; i < m; i++) {
		free(p[i]);
	}
	free(p);
	p = NULL;
}

void i32_VLArray2D_Destroy(int32_t** p, uint64_t m) {
	for (uint64_t i = 0; i < m; i++) {
		free(p[i]);
	}
	free(p);
	p = NULL;
}
