#ifndef _LIST_H_
#define _LIST_H_


typedef struct {
	unsigned int length;
	unsigned int alloc_length;
	unsigned short* List;
}u16_List;


typedef struct {
	unsigned int length;
	unsigned int alloc_length;
	unsigned long long* List;
}u64_List;


int u16_List_append(u16_List* src, unsigned short elem, unsigned int d_size);
int u64_List_append(u64_List* src, unsigned long long elem, unsigned int d_size);
int check_in_u16_List(unsigned short val, u16_List* src);


#endif
