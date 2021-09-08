#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"
#include "paint_up.h"
#include "list.h"


// unsigned char�������͵ĳ�ˮ�����λ���
int _paint_up_uint8(unsigned long long* idxs, unsigned char* colors, unsigned int idx_num, double frac,
	unsigned char* basin, unsigned char* re_dir, int rows, int cols) {

	uint64 cols64 = (uint64)cols;
	// �����ṩ�ı�����������Ҫ�õ���ջ��ȣ���Ҫ������quene����ջ��
	uint64 QUENE_SIZE = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (QUENE_SIZE > 100000000) {
		QUENE_SIZE = 100000000;
	}

	// ��ʼ��
	uint64 idx = 0;
	uint8 reverse_fdir = 0;
	uint8 color = 0;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_List quene = { 0,0,QUENE_SIZE,NULL };
	quene.List = (uint64*)calloc(QUENE_SIZE, sizeof(uint64));
	if (quene.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	quene.alloc_length = QUENE_SIZE;

	// ��һ�������Σ�����ƵĻḲ����ǰ�Ļ��ƽ����������Ҫע������������˳��
	for (uint i = 0; i < idx_num; i++) {

		idx = idxs[i];
		color = colors[i];

		// ����ջ
		quene.List[0] = idx;
		quene.length = 1;

		while (quene.length > 0) {
			// ��ջ��ɫ
			idx = quene.List[quene.length - 1];
			quene.length--;
			basin[idx] = color;
			// ������ջ
			reverse_fdir = re_dir[idx];
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_List_append(&quene, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
		}
	}

	// �ͷ��ڴ�
	free(quene.List);
	quene.List = NULL;
	quene.length = 0;
	quene.batch_size = 0;
	quene.alloc_length = 0;

	return 1;
}


// unsigned short�������͵ĳ�ˮ�����λ���
int _paint_up_uint16(unsigned long long* idxs, unsigned short* colors, unsigned int idx_num, double frac,
					 unsigned short* basin, unsigned char* re_dir, int rows, int cols) {

	uint64 cols64 = (uint64)cols;
	// �����ṩ�ı�����������Ҫ�õ���ջ��ȣ���Ҫ������quene����ջ��
	uint64 QUENE_SIZE = ((uint64)(rows * cols64 * frac / 10000) + 1) * 10000;
	if (QUENE_SIZE > 100000000) {
		QUENE_SIZE = 100000000;
	}

	// ��ʼ��
	uint64 idx = 0;
	uint8 reverse_fdir = 0;
	uint16 color;
	const uint8 div[8] = { 128,64,32,16,8,4,2,1 };
	const int offset[8] = { -cols + 1, -cols, -cols - 1, -1,-1 + cols,cols,cols + 1, 1 };
	u64_List quene = { 0,0,QUENE_SIZE,NULL };
	quene.List = (uint64*)calloc(QUENE_SIZE, sizeof(uint64));
	if (quene.List == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	quene.alloc_length = QUENE_SIZE;

	// ��һ�������Σ�����ƵĻḲ����ǰ�Ļ��ƽ����������Ҫע������������˳��
	for (uint i = 0; i < idx_num; i++) {

		idx = idxs[i];
		color = colors[i];

		// ����ջ
		quene.List[0] = idx;
		quene.length = 1;

		while (quene.length > 0) {
			// ��ջ��ɫ
			idx = quene.List[quene.length - 1];
			quene.length--;
			basin[idx] = color;
			// ������ջ
			reverse_fdir = re_dir[idx];
			for (int p = 0; p < 8; p++) {
				if (reverse_fdir >= div[p]) {
					u64_List_append(&quene, idx + offset[p]);
					reverse_fdir -= div[p];
				}
			}
		}
	}

	// �ͷ��ڴ�
	free(quene.List);
	quene.List = NULL;
	quene.length = 0;
	quene.batch_size = 0;
	quene.alloc_length = 0;

	return 1;
}
