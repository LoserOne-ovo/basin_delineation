#ifndef _PFS_ORIGIN_H_
#define _PFS_ORIGIN_H_



typedef struct {
	float upa;
	unsigned long long tri_idx;
	unsigned long long tru_idx;
}Tribu;


unsigned short* _dissolve_basin(unsigned char* dir, float* upa, float* dem, int rows, int cols, float ths,
							    unsigned long long outlet_idx, unsigned long long* sink_idxs, unsigned short sink_num);
unsigned short* _pfs_o_uint16(unsigned char* re_dir, float* upa, int rows, int cols, float ths, unsigned long long outlet_idx);
unsigned char* _pfs_o_uint8(unsigned char* dir, float* upa, int rows, int cols, float ths, unsigned long long outlet_idx);

int _tribu_insert(Tribu src[], float upa, unsigned long long tribu_idx, unsigned long long trunk_idx, float* min_upa, int* min_upa_probe);


#endif // !_PFS_ORIGIN_H_
