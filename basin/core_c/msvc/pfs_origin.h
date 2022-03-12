#ifndef _PFS_ORIGIN_H_
#define _PFS_ORIGIN_H_


typedef struct {
	float upa;
	unsigned long long tri_idx;
	unsigned long long tru_idx;
}Tribu;


int _tribu_insert(Tribu src[], float upa, unsigned long long tribu_idx, unsigned long long trunk_idx, float* min_upa, int* min_upa_probe);


#endif // !_PFS_ORIGIN_H_
