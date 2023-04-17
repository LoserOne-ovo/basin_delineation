#include <stdlib.h>
#include <stdio.h>
#include "Array.h"


/// <summary>
///     ����d8��������������
///     input array should be larger than 3*3
///     �����߲�������Ӧ����Ϊnodata.
/// </summary>
/// <param name="fdir">
///     1:��
///     2:����
///     4:��
///     8:����
///     16:��
///     32:����
///     64:��
///     128:����
/// </param>
/// <param name="rows">
///     ���������
/// </param>
/// <param name="cols">
///     ���������
/// </param>
/// <returns>
///     ���������
/// </returns>
uint8_t* _get_re_dir(uint8_t* __restrict fdir, int32_t rows, int32_t cols) {

    // ��������
    uint64_t cols64 = (uint64_t)cols;
    int32_t i = 0, j = 0;
    
    // ��ʼ�����������
    uint8_t* re_fdir = u8_VLArray_Initial(rows * cols64, 1);

    // ���Ĳ���
    uint64_t idx = cols64 + 1;
    uint8_t cur_dir;
    for (i = 1; i < rows - 1; i++) {
        for (j = 1; j < cols - 1; j++) {      
            cur_dir = fdir[idx];
            switch (cur_dir)
            {
            case 1:
                re_fdir[idx + 1] += 16;
                break;
            case 2:
                re_fdir[idx + cols + 1] += 32;
                break;
            case 4:
                re_fdir[idx + cols] += 64;
                break;
            case 8:
                re_fdir[idx + cols - 1] += 128;
                break;
            case 16:
                re_fdir[idx - 1] += 1;
                break;
            case 32:
                re_fdir[idx - cols - 1] += 2;
                break;
            case 64:
                re_fdir[idx - cols] += 4;
                break;
            case 128:
                re_fdir[idx - cols + 1] += 8;
                break;
            default:
                break;
            }
            ++idx; // ��һ����Ԫ
        }
        idx += 2; // ����
    }

    return re_fdir;
}


uint32_t _get_down_idx32(uint8_t loc_dir, uint32_t idx, int32_t cols) {

    switch (loc_dir)
    {
    case 1:
        return idx + 1;
    case 2:
        return idx + cols + 1;
    case 4:
        return idx + cols;
    case 8:
        return idx + cols - 1;
    case 16:
        return idx - 1;
    case 32:
        return idx - cols - 1;
    case 64:
        return idx - cols;
    case 128:
        return idx - cols + 1;
    default:
        return 0;
    }
}


uint64_t _get_down_idx64(uint8_t loc_dir, uint64_t idx, int32_t cols) {

    switch (loc_dir)
    {
    case 1:
        return idx + 1;
    case 2:
        return idx + cols + 1;
    case 4:
        return idx + cols;
    case 8:
        return idx + cols - 1;
    case 16:
        return idx - 1;
    case 32:
        return idx - cols - 1;
    case 64:
        return idx - cols;
    case 128:
        return idx - cols + 1;
    default:
        return 0;
    }
}


/// <summary>
/// ����һ����Ԫ��֪������d8���ε������ж�������Ԫ��������Ԫd8�����е�λ��
/// </summary>
/// <param name="upper_dir"></param>
/// <returns></returns>
uint8_t _get_up_dir(uint8_t upper_dir) {

    if (upper_dir >= 16) {
        upper_dir /= 16;
    }
    else
    {
        upper_dir *= 16;
    }
    return upper_dir;
}


/// <summary>
/// d8����˳ʱ�뷽�򣬼�����һ�������Ӧ�ı���
/// </summary>
/// <param name="dir"></param>
/// <returns></returns>
uint8_t _get_next_dir_clockwise(uint8_t dir) {

    if (dir == 128) {
        return 1;
    }
    else {
        return dir * 2;
    }
}
