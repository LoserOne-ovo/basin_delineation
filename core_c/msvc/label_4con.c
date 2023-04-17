/*
	Copyright: Nanjing Normal University (http://www.njnu.edu.cn/)
	Author: LoserOne-ovo (https://github.com/LoserOne-ovo)
*/


#include <stdlib.h>
#include <stdio.h>
#include "label_4con.h"


// �д��Ľ��Ĳ���
/*
	1. �г�ɨ������Ż�������Ҫ����һ���е�������ͨ�Ž��бȽϡ�
	��Լ���Լ���һ��ıȽϣ���ʱ�临�Ӷ�Ӧ�û���O(m*n)��
	��ÿһ����ͨ�Ž϶���龰�£��������Ż�����ġ�
	
	2. ����Ҫ���ٶ���Ŀռ�洢�ȼ۶ԡ����Ա��жϣ��߲�����
	ȱ���ǲ���Ԥ֪�ȼ۶���������Ԥ�ȿ����㹻��ĵȼ��б���̬�����ڴ档

*/

// reference: https://www.cnblogs.com/ronny/p/img_aly_01.html
/// <summary>
/// ��Ƕ�ֵͼ�������ͨ����
/// </summary>
/// <param name="bin_ima">��ά����flatten��һά����</param>
/// <param name="rows">��ά��������</param>
/// <param name="cols">��ά��������</param>
/// <param name="label_num">��������ͨ����������</param>
/// <returns>�������ǽ��</returns>
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
    // Ϊ���б�����ڴ�
    if (tuple_list == NULL) {
        fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
        exit(-1);
    }
    // ��ʼ��
    for (int32_t i = 0; i < rows; i++) {
        tuple_list[i].length = 0;
        tuple_list[i].data = (con_tuple*)calloc(TUPLE_SIZE, sizeof(con_tuple));
        tuple_list[i].alloc_length = TUPLE_SIZE;
    }

    // ��ʼ���ȼ۱��������ڴ�
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

    // ��һ��
    for (int32_t j = 0; j < cols; j++) {
        
        if (bin_ima[idx] == 1) {

            // ��һ����ͨ�ŵ�����
            if (flag_con) {
                ;
            }
            // һ���µ���ͨ��
            else {
                start_idx = j;
                flag_con = 1;
            }
        }
        else if (bin_ima[idx] == 0) {

            // һ����ͨ�ŵĽ���
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
            // δ�����µ���ͨ��
            else {
                ;
            }
        }
        idx++;
    }
    // �жϵ�һ��ĩβ�Ƿ�����ͨ��
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

    // �ڶ��е����һ��
    for (int32_t i = 1; i < rows; i++) {

        for (int32_t j = 0; j < cols; j++) {
  
            if (bin_ima[idx] == 1) {

                // ��һ����ͨ�ŵ�����
                if (flag_con) {
                    ;
                }
                // һ���µ���ͨ��
                else {
                    start_idx = j;
                    flag_con = 1;
                }
            }
            else if (bin_ima[idx] == 0) {

                // һ����ͨ�ŵĽ���
                if (flag_con) {
                    end_idx = j - 1;
                    check_rList_alloc(&tuple_list[i]);
                    temp_len = tuple_list[i].length;
                    tuple_list[i].length += 1;
                    tuple_list[i].data[temp_len].s_cidx = start_idx;
                    tuple_list[i].data[temp_len].e_cidx = end_idx;

                    // �ж�Ҫ����ı��
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
                // δ�����µ���ͨ�ţ���������

            }
            idx++;
        }
        // �ж�ÿһ��ĩβ�Ƿ�����ͨ��
        if (flag_con) {

            end_idx = cols - 1;
            check_rList_alloc(&tuple_list[i]);
            temp_len = tuple_list[i].length;
            tuple_list[i].length += 1;
            tuple_list[i].data[temp_len].s_cidx = start_idx;
            tuple_list[i].data[temp_len].e_cidx = end_idx;

            // �ж�Ҫ����ı��
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
    *     �����ȼ۶�     *
    **********************/

    if (tuple_tag > 1) {
        
        int32_t* dissolved_tags = i32_VLArray_Initial(tuple_tag, 1);
        int32_t loc_tag, pre_tag, backup = 0;

		// �����ȼ۶��б�
		for (i = 0; i < ecList->length; i++) {
			loc_tag = ecList->data[i].max_tag;
			pre_tag = ecList->data[i].min_tag;
			while ((dissolved_tags[loc_tag] != 0) && (dissolved_tags[loc_tag] != pre_tag)) {
				// �����µĵȼ۶�
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
			// �޷�Ѱ�ҵ��µĵȼ۶�
			if (dissolved_tags[loc_tag] == 0) {
				dissolved_tags[loc_tag] = pre_tag;
			}
		}

        // ��ʱ���ж���Ϊ0���������ж��ٸ����ڵ�
        // ��Ϊÿһ���ȼ��б���С�������ǰ��,���Դ�ǰ����ֵֻ��Ҫ��ǰһ����ֵ����
        for (i = 1; i < tuple_tag; i++) {
            if (dissolved_tags[i] == 0) {
                dissolved_tags[i] = ++root_num;
            }
            else {
                dissolved_tags[i] = dissolved_tags[dissolved_tags[i]];
            }
        }

        // �����ؽ����ֵ
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
                } // ����һ���е�һ����ͨ�ŵĸ�ֵ
            } // ����һ�еĸ�ֵ
        } // �������еĸ�ֵ

        // �ͷ��ڴ�
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

    // �ж��Ƿ���Ҫ���·����ڴ�
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

        // ������ſ�,�Ƿ�����һ�е������ſ�,����ֱ���������ص��Ĳ���

        for (int32_t i = 0; i < dump_num; i++) {

            left_edge = rList->data[i].s_cidx;
            right_edge = rList->data[i].e_cidx;

            // ����ص���
            if (line_intersection(left_edge, right_edge, start_idx, end_idx)) {
                // �Ѿ����ص��Ĳ��֣���¼�ȼ۶ԣ�������б��
                if (flag_overlap) {
                    add_ec(ecList, tag_return, rList->data[i].tag_idx);
                }
                // ��һ���ص������б�ǣ�����¼�ȼ۶�
                else {
                    tag_return = rList->data[i].tag_idx;
                    flag_overlap = 1;
                }
            }
        }
    }

    // ���û���ص��Ĳ���,�򷵻�0����ζ�ų������µĶ����ſ飬tuple_tag��Ҫ��������������
    return tag_return;
}


int32_t line_intersection(int32_t a1, int32_t a2, int32_t b1, int32_t b2) {

    // a�߶�����
    if (a1 <= b1) {
        if (b1 <= a2) {
            return 1;
        }
        else {
            return 0;
        }
    }
    // b�߶θ�����
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
        // ���ֵ��ͬ�������¼�ȼ۶�
    }
    else {
        // ���ֵ��ͬ����¼�ȼ۶�

        // ���ж��Ƿ���Ҫ���·����ڴ�
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

        // �ж��ĸ�tagֵ����
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


