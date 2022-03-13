#include "interfaces.h"
#include "type_aka.h"
#include <stdio.h>
#include <stdlib.h>


/***********************************
 *          shared part            *
 ***********************************/

unsigned int* label_4con(unsigned char* bin_ima, int rows, int cols, unsigned int* label_num) {

	return _label_4con(bin_ima, rows, cols, label_num);
}


unsigned char* calc_reverse_fdir(unsigned char* fdir, int rows, int cols) {

	return _get_re_dir(fdir, rows, cols);
}


int get_basin_envelope_uint8(unsigned char* basin, int* envelopes, int rows, int cols) {

	return _get_basin_envelope_uint8(basin, envelopes, rows, cols);
}



/************************************
 *           island part            *
 ************************************/

int island_statistic_uint32(unsigned int* island_label, unsigned int island_num, float* center, int* sample,  float* radius,
							float* area, float* ref_area, int* envelope, unsigned char* dir, float* upa, int rows, int cols) {

	return _calc_island_statistics_uint32(island_label, island_num, center, sample, radius, area, ref_area, envelope, dir, upa, rows, cols);
}


int update_island_label_uint32(unsigned int* island_label, unsigned int* new_label, unsigned int island_num, int rows, int cols) {

	return _update_island_label_uint32(island_label, island_num, new_label, rows, cols);
}




/***********************************
 *          outlet part            *
 ***********************************/

int pfafstetter(int outlet_ridx, int outlet_cidx, unsigned char* basin, unsigned char* re_dir, float* upa,
			    int* sub_outlets, float ths, int rows, int cols) {

	return _pfs_r_uint8(outlet_ridx, outlet_cidx, basin, re_dir, upa, sub_outlets, ths, rows, cols);
}




/***********************************
 *           paint part            *
 ***********************************/

int paint_up_uint8(unsigned long long* idxs, unsigned char* colors, unsigned int idx_num, double frac,
				   unsigned char* basin, unsigned char* re_dir, int rows, int cols) {

	return _paint_up_uint8(idxs, colors, idx_num, frac, basin, re_dir, rows, cols);
}


int paint_up_mosaiced_uint8(int* ridx, int* cidx, unsigned int num, double frac, unsigned char* basin, 
						    unsigned char* re_dir, int rows, int cols) {


	uint64 cols64 = (uint64)cols;
	uint64* idxs_1D = (uint64*)calloc(num, sizeof(unsigned long long));
	if (idxs_1D == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint i = 0; i < num; i++) {
		idxs_1D[i] = ridx[i] * cols64 + cidx[i];
	}

	uint8* colors = (uint8*)calloc(num, sizeof(unsigned char));
	if (colors == NULL) {
		fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
		exit(-1);
	}
	for (uint i = 0; i < num; i++) {
		colors[i] = basin[idxs_1D[i]];
	}

	int res = _paint_up_uint8(idxs_1D, colors, num, frac, basin, re_dir, rows, cols);
	free(idxs_1D);
	free(colors);

	return res;
}


/***********************************
 *           sink part             *
 ***********************************/

int dissolve_sinks_uint8(unsigned char* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
						 unsigned char sink_num, int rows, int cols, double frac) {

	return _dissolve_sinks_uint8(basin, re_dir, dem, sink_idxs, sink_num, rows, cols, frac);
}

int dissolve_sinks_uint16(unsigned short* basin, unsigned char* re_dir, float* dem, unsigned long long* sink_idxs,
						  unsigned short sink_num, int rows, int cols, double frac) {

	return _dissolve_sinks_uint16(basin, re_dir, dem, sink_idxs, sink_num, rows, cols, frac);
}