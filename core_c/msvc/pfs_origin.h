#ifndef _PFS_ORIGIN_H_
#define _PFS_ORIGIN_H_

#include <stdint.h>


typedef struct {
	float upa;
	uint64_t tri_idx; // tributary
	uint64_t tru_idx; // trunk stream
	uint64_t nex_idx; // nexus
}Tribu;


int32_t _tribu_insert(Tribu src[], float upa, uint64_t* node, float* min_upa, int32_t* min_upa_probe);


#endif // !_PFS_ORIGIN_H_
