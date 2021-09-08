#ifndef _LIST_H_
#define _LIST_H_


typedef struct {
	unsigned long long length;
	unsigned long long alloc_length;
	unsigned long long batch_size;
	unsigned char* List;
}u8_List;


typedef struct {
	unsigned long long length;
	unsigned long long alloc_length;
	unsigned long long batch_size;
	unsigned short* List;
}u16_List;


typedef struct {
	unsigned long long length;
	unsigned long long alloc_length;
	unsigned long long batch_size;
	unsigned long long* List;
}u64_List;


int u8_List_append(u8_List* src, unsigned char elem);
int u16_List_append(u16_List* src, unsigned short elem);
int u64_List_append(u64_List* src, unsigned long long elem);
int check_in_u16_List(unsigned short val, u16_List* src);
int check_in_u8_List(unsigned char val, u8_List* src);


#endif
