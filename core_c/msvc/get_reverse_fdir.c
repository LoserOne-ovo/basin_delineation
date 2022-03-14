#include <stdlib.h>
#include <stdio.h>
#include "type_aka.h"


/// <summary>
///     根据d8流向，生成逆流向
///     input array should be larger than 3*3
///     1个点
/// </summary>
/// <param name="fdir">
///     0:代表海陆交界
///     1:右
///     2:右下
///     4:下
///     8:左下
///     16:左
///     32:左上
///     64:上
///     128:右上
///     247:海洋
///     255:洼地
/// </param>
/// <param name="rows">
///     矩阵的行数
/// </param>
/// <param name="cols">
///     矩阵的列数
/// </param>
/// <returns>
///     逆流向矩阵
/// </returns>
unsigned char* _get_re_dir(unsigned char* fdir, int rows, int cols) {

    uint64 cols64 = (uint64)cols;
    unsigned char nodata = 255;
    uint64 idx = 0;

    unsigned char* re_fdir = (unsigned char*)calloc(rows * cols64, sizeof(unsigned char));
    if (re_fdir == NULL) {
        fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
        exit(-1);
    }
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            re_fdir[idx++] = 0;
        }
    }

    // 中心部分
    for (int i = 1; i < rows - 1; i++) {
        for (int j = 1; j < cols - 1; j++) {
            idx = i * cols64 + j;
            if (fdir[idx] == nodata || fdir[idx] == 0 || fdir[idx] == 247) { ; }
            else {
                if (fdir[idx] == 1) {
                    // 向右流，右侧的栅格加上16
                    re_fdir[idx + 1] += 16;
                }
                else if (fdir[idx] == 2) {
                    // 向右下流， 右下的栅格加上32
                    re_fdir[idx + cols + 1] += 32;
                }
                else if (fdir[idx] == 4) {
                    // 向下流， 下方的栅格加上64
                    re_fdir[idx + cols] += 64;
                }
                else if (fdir[idx] == 8) {
                    // 向左下流， 左下的栅格加上128
                    re_fdir[idx + cols - 1] += 128;
                }
                else if (fdir[idx] == 16) {
                    // 向左流， 左侧的栅格加上1
                    re_fdir[idx - 1] += 1;
                }
                else if (fdir[idx] == 32) {
                    // 向左上流， 左上的栅格加上2
                    re_fdir[idx - cols - 1] += 2;
                }
                else if (fdir[idx] == 64) {
                    // 向上流， 上方的栅格加上4
                    re_fdir[idx - cols] += 4;
                }
                else if (fdir[idx] == 128) {
                    // 向右上流， 右上的栅格加上8
                    re_fdir[idx - cols + 1] += 8;
                }
                else {
                    // 不应该出现的情况
                    ;
                }

            }
        }
    }

    return re_fdir;

}


unsigned int _get_down_idx32(unsigned char loc_dir, unsigned int idx, int cols) {

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


unsigned long long _get_down_idx64(unsigned char loc_dir, unsigned long long idx, int cols) {

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
/// 对于一个像元，知道它的d8上游的流向，判断上游像元在下游像元d8流域中的位置
/// </summary>
/// <param name="upper_dir"></param>
/// <returns></returns>
unsigned char _get_up_dir(unsigned char upper_dir) {

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
/// d8，沿顺时针方向，计算下一个流向对应的编码
/// </summary>
/// <param name="dir"></param>
/// <returns></returns>
unsigned char _get_next_dir_clockwise(unsigned char dir) {

    if (dir == 128) {
        return 1;
    }
    else {
        return dir * 2;
    }
}
