#ifndef _ARRAY_H_
#define _ARRAY_H_

#include <stdint.h>


typedef struct {
	uint64_t length;
	uint64_t alloc_length;
	uint64_t batch_size;
	uint8_t* data;
}u8_DynArray;


typedef struct {
	uint64_t length;
	uint64_t alloc_length;
	uint64_t batch_size;
	uint16_t* data;
}u16_DynArray;


typedef struct {
	uint64_t length;
	uint64_t alloc_length;
	uint64_t batch_size;
	uint32_t* data;
}u32_DynArray;


typedef struct {
	uint64_t length;
	uint64_t alloc_length;
	uint64_t batch_size;
	uint64_t* data;
}u64_DynArray;


typedef struct {
	uint64_t length;
	uint64_t alloc_length;
	uint64_t batch_size;
	int32_t* data;
}i32_DynArray;


u8_DynArray* u8_DynArray_Initial(uint64_t length);
u16_DynArray* u16_DynArray_Initial(uint64_t length);
u32_DynArray* u32_DynArray_Initial(uint64_t length);
u64_DynArray* u64_DynArray_Initial(uint64_t length);
i32_DynArray* i32_DynArray_Initial(uint64_t length);


void u8_DynArray_Destroy(u8_DynArray* p);
void u16_DynArray_Destroy(u16_DynArray* p);
void u32_DynArray_Destroy(u32_DynArray* p);
void u64_DynArray_Destroy(u64_DynArray* p);
void i32_DynArray_Destroy(i32_DynArray* p);


int32_t u8_DynArray_Push(u8_DynArray* src, uint8_t elem);
int32_t u16_DynArray_Push(u16_DynArray* src, uint16_t elem);
int32_t u32_DynArray_Push(u32_DynArray* src, uint32_t elem);
int32_t u64_DynArray_Push(u64_DynArray* src, uint64_t elem);
int32_t i32_DynArray_Push(i32_DynArray* src, int32_t elem);


int32_t check_in_u8_DynArray(uint8_t val, u8_DynArray* src);
int32_t check_in_u16_DynArray(uint16_t val, u16_DynArray* src);
int32_t check_in_u32_DynArray(uint32_t val, u32_DynArray* src);
int32_t check_in_u64_DynArray(uint64_t val, u64_DynArray* src);
int32_t check_in_i32_DynArray(int32_t val, i32_DynArray* src);


uint8_t** u8_VLArray2D_Initial(uint64_t m, uint64_t n, int32_t flag);
int32_t** i32_VLArray2D_Initial(uint64_t m, uint64_t n, int32_t flag);

uint8_t* u8_VLArray_Initial(uint64_t m, int32_t flag);
uint16_t* u16_VLArray_Initial(uint64_t m, int32_t flag);
int32_t* i32_VLArray_Initial(uint64_t m, int32_t flag);
uint64_t* u64_VLArray_Initial(uint64_t m, int32_t flag);
float* f32_VLArray_Initial(uint64_t m, int32_t flag);

void u8_VLArray2D_Destroy(uint8_t** p, uint64_t m);
void i32_VLArray2D_Destroy(int32_t** p, uint64_t m);


#endif

