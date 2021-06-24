#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"

/// <summary>
///     ����d8��������������
///     input array should be larger than 3*3
///     1����
/// </summary>
/// <param name="fdir">
///     0:����½����
///     1:��
///     2:����
///     4:��
///     8:����
///     16:��
///     32:����
///     64:��
///     128:����
///     247:����
///     255:�ݵ�
/// </param>
/// <param name="rows">
///     ���������
/// </param>
/// <param name="cols">
///     ���������
/// </param>
/// /// <param name="nodata">
///     դ���nodataֵ
/// </param>
/// <returns>
///     ���������
/// </returns>
__declspec(dllexport) unsigned char* reverse_fdir(unsigned char* fdir, int rows, int cols) {

    uint64 cols64 = (uint64)cols;
    unsigned char nodata = 255;
    uint64 idx = 0;

    unsigned char* re_fdir = (unsigned char*)calloc(rows * cols64, sizeof(unsigned char));
    if (re_fdir == NULL) {
        fprintf(stderr, "memory reallocation failed!\r\n");
        exit(-1);
    }
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            re_fdir[idx++] = 0;
        }
    }

    // ���Ĳ���
    for (int i = 1; i < rows - 1; i++) {
        for (int j = 1; j < cols - 1; j++) {
            idx = i * cols64 + j;
            if (fdir[idx] == nodata || fdir[idx] == 0 || fdir[idx] == 247) { ; }
            else {
                if (fdir[idx] == 1) {
                    // ���������Ҳ��դ�����16
                    re_fdir[idx + 1] += 16;
                }
                else if (fdir[idx] == 2) {
                    // ���������� ���µ�դ�����32
                    re_fdir[idx + cols + 1] += 32;
                }
                else if (fdir[idx] == 4) {
                    // �������� �·���դ�����64
                    re_fdir[idx + cols] += 64;
                }
                else if (fdir[idx] == 8) {
                    // ���������� ���µ�դ�����128
                    re_fdir[idx + cols - 1] += 128;
                }
                else if (fdir[idx] == 16) {
                    // �������� ����դ�����1
                    re_fdir[idx - 1] += 1;
                }
                else if (fdir[idx] == 32) {
                    // ���������� ���ϵ�դ�����2
                    re_fdir[idx - cols - 1] += 2;
                }
                else if (fdir[idx] == 64) {
                    // �������� �Ϸ���դ�����4
                    re_fdir[idx - cols] += 4;
                }
                else if (fdir[idx] == 128) {
                    // ���������� ���ϵ�դ�����8
                    re_fdir[idx - cols + 1] += 8;
                }
                else {
                    // ��Ӧ�ó��ֵ����
                    ;
                }

            }
        }
    }

    return re_fdir;

}