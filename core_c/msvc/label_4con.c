/*
	Copyright: Nanjing Normal University (http://www.njnu.edu.cn/)
	Author: LoserOne-ovo (https://github.com/LoserOne-ovo)
*/


#include <stdlib.h>
#include <stdio.h>
#include "label_4con.h"


// 有待改进的部分
/*
	1. 行程扫描可以优化，不需要和上一行中的所有连通团进行比较。
	大约可以减少一般的比较，但时间复杂度应该还是O(m*n)。
	在每一行连通团较多的情景下，还是有优化意义的。
	
	2. 不需要开辟额外的空间存储等价对。可以边判断，边操作。
	缺点是不能预知等价对数量，得预先开辟足够大的等价列表，或动态分配内存。

*/

// reference: https://www.cnblogs.com/ronny/p/img_aly_01.html
/// <summary>
/// 标记二值图像的四连通区域
/// </summary>
/// <param name="bin_ima">二维矩阵flatten成一维矩阵</param>
/// <param name="rows">二维矩阵行数</param>
/// <param name="cols">二维矩阵列数</param>
/// <param name="label_num">返回四连通区域标记数量</param>
/// <returns>四连域标记结果</returns>
int32_t* _label_4con(uint8_t* __restrict bin_ima, int32_t rows, int32_t cols, int32_t* label_num) {

    int32_t root_num = 0;
    uint64_t cols64 = (uint64_t)cols;
    uint64_t total = rows * cols64;
    int32_t i = 0, j = 0;

    int32_t* __restrict result = (int32_t*)calloc(total, sizeof(int32_t));
    if (result == NULL) {
        fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
        exit(-1);
    }

    tuple_row* tuple_list = (tuple_row*)calloc(rows, sizeof(tuple_row));
    // 为团列表分配内存
    if (tuple_list == NULL) {
        fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
        exit(-1);
    }
    // 初始化
    for (int32_t i = 0; i < rows; i++) {
        tuple_list[i].length = 0;
        tuple_list[i].data = (con_tuple*)calloc(TUPLE_SIZE, sizeof(con_tuple));
        tuple_list[i].alloc_length = TUPLE_SIZE;
    }

    // 初始化等价表，并分配内存
    equ_couple_list* ecList = (equ_couple_list*)malloc(sizeof(equ_couple_list));
    if (ecList == NULL) {
        fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
        exit(-1);
    }
    ecList->length = 0;
    ecList->data = (equ_couple*)calloc(EC_SIZE, sizeof(equ_couple));
    if (ecList->data == NULL) {
        fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
        exit(-1);
    }
    ecList->alloc_length = EC_SIZE;

    int32_t start_idx = 0;
    int32_t end_idx = 0;
    int32_t flag_con = 0;
    int32_t temp_len = 0;
    int32_t tuple_tag = 1;
    int32_t temp_tag = 0;
    uint64_t idx = 0;

    // 第一行
    for (int32_t j = 0; j < cols; j++) {
        
        if (bin_ima[idx] == 1) {

            // 上一个连通团的延续
            if (flag_con) {
                ;
            }
            // 一个新的连通团
            else {
                start_idx = j;
                flag_con = 1;
            }
        }
        else if (bin_ima[idx] == 0) {

            // 一个连通团的结束
            if (flag_con) {
                end_idx = j - 1;
                check_rList_alloc(&tuple_list[0]);
                temp_len = tuple_list[0].length;
                tuple_list[0].length += 1;
                tuple_list[0].data[temp_len].s_cidx = start_idx;
                tuple_list[0].data[temp_len].e_cidx = end_idx;

                tuple_list[0].data[temp_len].tag_idx = tuple_tag;
                tuple_tag++;

                flag_con = 0;

            }
            // 未发现新的连通团
            else {
                ;
            }
        }
        idx++;
    }
    // 判断第一行末尾是否有连通团
    if (flag_con) {

        end_idx = cols - 1;
        check_rList_alloc(&tuple_list[0]);
        temp_len = tuple_list[0].length;
        tuple_list[0].length += 1;
        tuple_list[0].data[temp_len].s_cidx = start_idx;
        tuple_list[0].data[temp_len].e_cidx = end_idx;

        tuple_list[0].data[temp_len].tag_idx = tuple_tag;
        tuple_tag++;

        flag_con = 0;
    }

    // 第二行到最后一行
    for (int32_t i = 1; i < rows; i++) {

        for (int32_t j = 0; j < cols; j++) {
  
            if (bin_ima[idx] == 1) {

                // 上一个连通团的延续
                if (flag_con) {
                    ;
                }
                // 一个新的连通团
                else {
                    start_idx = j;
                    flag_con = 1;
                }
            }
            else if (bin_ima[idx] == 0) {

                // 一个连通团的结束
                if (flag_con) {
                    end_idx = j - 1;
                    check_rList_alloc(&tuple_list[i]);
                    temp_len = tuple_list[i].length;
                    tuple_list[i].length += 1;
                    tuple_list[i].data[temp_len].s_cidx = start_idx;
                    tuple_list[i].data[temp_len].e_cidx = end_idx;

                    // 判断要赋予的编号
                    temp_tag = get_tag(&(tuple_list[i - 1]), start_idx, end_idx, ecList);
                    if (temp_tag == 0) {
                        tuple_list[i].data[temp_len].tag_idx = tuple_tag;
                        tuple_tag++;
                    }
                    else {
                        tuple_list[i].data[temp_len].tag_idx = temp_tag;
                    }

                    flag_con = 0;

                }
                // 未发现新的连通团，不做处理

            }
            idx++;
        }
        // 判断每一行末尾是否有连通团
        if (flag_con) {

            end_idx = cols - 1;
            check_rList_alloc(&tuple_list[i]);
            temp_len = tuple_list[i].length;
            tuple_list[i].length += 1;
            tuple_list[i].data[temp_len].s_cidx = start_idx;
            tuple_list[i].data[temp_len].e_cidx = end_idx;

            // 判断要赋予的编号
            temp_tag = get_tag(&(tuple_list[i - 1]), start_idx, end_idx, ecList);
            if (temp_tag == 0) {
                tuple_list[i].data[temp_len].tag_idx = tuple_tag;
                tuple_tag++;
            }
            else {
                tuple_list[i].data[temp_len].tag_idx = temp_tag;
            }

            flag_con = 0;
        }
    }

    /*********************
    *     消除等价对     *
    **********************/

    if (tuple_tag > 1) {
        
        int32_t* dissolved_tags = i32_VLArray_Initial(tuple_tag, 1);
        int32_t loc_tag, pre_tag, backup = 0;

		// 遍历等价对列表
		for (i = 0; i < ecList->length; i++) {
			loc_tag = ecList->data[i].max_tag;
			pre_tag = ecList->data[i].min_tag;
			while ((dissolved_tags[loc_tag] != 0) && (dissolved_tags[loc_tag] != pre_tag)) {
				// 生成新的等价对
				backup = dissolved_tags[loc_tag];
                if (dissolved_tags[loc_tag] < pre_tag) {
                    loc_tag = pre_tag;
                    pre_tag = backup;
                }
                else {
                    dissolved_tags[loc_tag] = pre_tag;
                    loc_tag = backup;
                }
			}
			// 无法寻找到新的等价对
			if (dissolved_tags[loc_tag] == 0) {
				dissolved_tags[loc_tag] = pre_tag;
			}
		}

        // 此时，有多少为0的数，就有多少个根节点
        // 因为每一个等价列表都是小的序号在前面,所以从前往后赋值只需要找前一个的值即可
        for (i = 1; i < tuple_tag; i++) {
            if (dissolved_tags[i] == 0) {
                dissolved_tags[i] = ++root_num;
            }
            else {
                dissolved_tags[i] = dissolved_tags[dissolved_tags[i]];
            }
        }

        // 给返回结果赋值
        int32_t dump_num = 0;
        for (int32_t i = 0; i < rows; i++) {
            dump_num = tuple_list[i].length;
            for (int32_t j = 0; j < dump_num; j++) {
                start_idx = tuple_list[i].data[j].s_cidx;
                end_idx = tuple_list[i].data[j].e_cidx;
                temp_tag = dissolved_tags[tuple_list[i].data[j].tag_idx];
                for (int32_t m = start_idx; m < end_idx + 1; m++) {
                    idx = cols64 * i + m;
                    result[idx] = temp_tag;
                } // 结束一行中的一块连通团的赋值
            } // 结束一行的赋值
        } // 结束所有的赋值

        // 释放内存
        free(dissolved_tags);
    }

    for (int32_t i = 0; i < rows; i++) {
        free(tuple_list[i].data);
        tuple_list[i].data = NULL;
    }
    free(tuple_list);
    free(ecList->data);
    free(ecList);

    *label_num = root_num;
    return result;

}


void check_rList_alloc(tuple_row* rList) {

    // 判断是否需要重新分配内存
    if (rList->length == rList->alloc_length) {

        int32_t new_size = rList->alloc_length + TUPLE_SIZE;
        con_tuple* tem_p = (con_tuple*)realloc(rList->data, new_size * sizeof(con_tuple));
        if (tem_p == NULL) {
            fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
            exit(-1);
        }
        else {
            rList->data = tem_p;
            rList->alloc_length = new_size;
        }
    }
}


int32_t get_tag(tuple_row* rList, int32_t start_idx, int32_t end_idx, equ_couple_list* ecList) {

    int32_t tag_return = 0;
    int32_t dump_num = rList->length;
    if (dump_num == 0) {
        return tag_return;
    }
    else {

        int32_t flag_overlap = 0;
        int32_t left_edge = 0, right_edge = 0;

        // 看这个团块,是否与上一行的所有团块,在竖直方向上有重叠的部分

        for (int32_t i = 0; i < dump_num; i++) {

            left_edge = rList->data[i].s_cidx;
            right_edge = rList->data[i].e_cidx;

            // 如果重叠了
            if (line_intersection(left_edge, right_edge, start_idx, end_idx)) {
                // 已经有重叠的部分，记录等价对，无需进行标记
                if (flag_overlap) {
                    add_ec(ecList, tag_return, rList->data[i].tag_idx);
                }
                // 第一次重叠，进行标记，不记录等价对
                else {
                    tag_return = rList->data[i].tag_idx;
                    flag_overlap = 1;
                }
            }
        }
    }

    // 如果没有重叠的部分,则返回0；意味着出现了新的独立团块，tuple_tag需要进行自增操作。
    return tag_return;
}


int32_t line_intersection(int32_t a1, int32_t a2, int32_t b1, int32_t b2) {

    // a线段在左
    if (a1 <= b1) {
        if (b1 <= a2) {
            return 1;
        }
        else {
            return 0;
        }
    }
    // b线段更靠左
    else {
        if (a1 <= b2) {
            return 1;
        }
        else {
            return 0;
        }
    }

}


void add_ec(equ_couple_list* ecList, int32_t tag_a, int32_t tag_b) {

    if (tag_a == tag_b) {
        // 标记值相同，无需记录等价对
    }
    else {
        // 标记值不同，记录等价对

        // 先判断是否需要重新分配内存
        if (ecList->length == ecList->alloc_length) {
            int32_t new_size = ecList->alloc_length + EC_SIZE;
            equ_couple* tem_p = (equ_couple*)realloc(ecList->data, new_size * sizeof(equ_couple));
            if (tem_p == NULL) {
                fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
                exit(-1);
            }
            else {
                ecList->data = tem_p;
                ecList->alloc_length = new_size;
            }
        }

        // 判断哪个tag值更大
        if (tag_a < tag_b) {
            ecList->data[ecList->length].min_tag = tag_a;
            ecList->data[ecList->length].max_tag = tag_b;
            ecList->length++;
        }
        else {
            ecList->data[ecList->length].min_tag = tag_b;
            ecList->data[ecList->length].max_tag = tag_a;
            ecList->length++;
        }

    }

}


