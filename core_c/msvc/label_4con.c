/*
	Copyright: Nanjing Normal University (http://www.njnu.edu.cn/)
	Author: LoserOne-ovo (https://github.com/LoserOne-ovo)
*/


#include <stdlib.h>
#include <stdio.h>
#include "label_4con.h"
#include "type_aka.h"


// �д��Ľ��Ĳ���
/*
	1. �г�ɨ������Ż�������Ҫ����һ���е�������ͨ�Ž��бȽϡ�
	��Լ���Լ���һ��ıȽϣ���ʱ�临�Ӷ�Ӧ�û���O(m*n)��
	��ÿһ����ͨ�Ž϶���龰�£��������Ż�����ġ�
	
	2. ����Ҫ���ٶ���Ŀռ�洢�ȼ۶ԡ����Ա��жϣ��߲�����
	ȱ���ǲ���Ԥ֪�ȼ۶���������Ԥ�ȿ����㹻��ĵȼ��б���̬�����ڴ档

	3. ��Ȼ������Ҫsolved_tags������ֻʹ��dissolved_tags��

*/


/// <summary>
/// ��Ƕ�ֵͼ�������ͨ����
/// </summary>
/// <param name="bin_ima">��ά����flatten��һά����</param>
/// <param name="rows">��ά��������</param>
/// <param name="cols">��ά��������</param>
/// <param name="label_num">��������ͨ����������</param>
/// <returns>�������ǽ��</returns>
unsigned int* _label_4con(unsigned char* __restrict bin_ima, int rows, int cols, unsigned int* label_num) {

    // reference: https://www.cnblogs.com/ronny/p/img_aly_01.html

    uint64 cols64 = (uint64)cols;
    
    // ��ʼ�����ؽ��Ϊ0
    uint root_num = 0;
    uint64 total = rows * cols64;
    uint* __restrict result = (unsigned int*)calloc(total, sizeof(unsigned int));
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
    for (int i = 0; i < rows; i++) {
        tuple_list[i].length = 0;
        tuple_list[i].List = (con_tuple*)calloc(TUPLE_SIZE, sizeof(con_tuple));
        tuple_list[i].alloc_length = TUPLE_SIZE;
    }

    // ��ʼ���ȼ۱��������ڴ�
    equ_couple_list* ecList = (equ_couple_list*)malloc(sizeof(equ_couple_list));
    if (ecList == NULL) {
        fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
        exit(-1);
    }
    ecList->length = 0;
    ecList->List = (equ_couple*)calloc(EC_SIZE, sizeof(equ_couple));
    if (ecList->List == NULL) {
        fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
        exit(-1);
    }
    ecList->alloc_length = EC_SIZE;

    uint start_idx = 0;
    uint end_idx = 0;
    uint64 idx = 0;
    int flag_con = 0;
    uint temp_len = 0;
    uint tuple_tag = 1;
    uint temp_tag = 0;

    // ��һ��
    for (int j = 0; j < cols; j++) {
        
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
                tuple_list[0].List[temp_len].s_cidx = start_idx;
                tuple_list[0].List[temp_len].e_cidx = end_idx;

                tuple_list[0].List[temp_len].tag_idx = tuple_tag;
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
        tuple_list[0].List[temp_len].s_cidx = start_idx;
        tuple_list[0].List[temp_len].e_cidx = end_idx;

        tuple_list[0].List[temp_len].tag_idx = tuple_tag;
        tuple_tag++;

        flag_con = 0;
    }

    // �ڶ��е����һ��
    for (int i = 1; i < rows; i++) {

        for (int j = 0; j < cols; j++) {
  
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
                    tuple_list[i].List[temp_len].s_cidx = start_idx;
                    tuple_list[i].List[temp_len].e_cidx = end_idx;

                    // �ж�Ҫ����ı��
                    temp_tag = get_tag(&(tuple_list[i - 1]), start_idx, end_idx, ecList);
                    if (temp_tag == 0) {
                        tuple_list[i].List[temp_len].tag_idx = tuple_tag;
                        tuple_tag++;
                    }
                    else {
                        tuple_list[i].List[temp_len].tag_idx = temp_tag;
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
            tuple_list[i].List[temp_len].s_cidx = start_idx;
            tuple_list[i].List[temp_len].e_cidx = end_idx;

            // �ж�Ҫ����ı��
            temp_tag = get_tag(&(tuple_list[i - 1]), start_idx, end_idx, ecList);
            if (temp_tag == 0) {
                tuple_list[i].List[temp_len].tag_idx = tuple_tag;
                tuple_tag++;
            }
            else {
                tuple_list[i].List[temp_len].tag_idx = temp_tag;
            }

            flag_con = 0;
        }
    }

    /*********************
    *     �����ȼ۶�     *
    **********************/

    if (tuple_tag > 1) {

        unsigned int* __restrict dissolved_tags = (unsigned int*)calloc(tuple_tag, sizeof(unsigned int));
        if (dissolved_tags == NULL) {
            fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
            exit(-1);
        }
        unsigned int* __restrict solved_tags = (unsigned int*)calloc(tuple_tag, sizeof(unsigned int));
        if (solved_tags == NULL) {
            fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
            exit(-1);
        }
        unsigned int loc_tag, pre_tag, backup = 0;

		// �����ȼ۶��б�
		for (uint i = 0; i < ecList->length; i++) {

			loc_tag = ecList->List[i].max_tag;
			pre_tag = ecList->List[i].min_tag;

			while ((dissolved_tags[loc_tag] != 0) && (dissolved_tags[loc_tag] != pre_tag)) {
				// �����µĵȼ۶�
				backup = dissolved_tags[loc_tag];
				dissolved_tags[loc_tag] = min_uint(dissolved_tags[loc_tag], pre_tag);
				loc_tag = max_uint(backup, pre_tag);
				pre_tag = min_uint(backup, pre_tag);
			}

			// �޷�Ѱ�ҵ��µĵȼ۶�
			if (dissolved_tags[loc_tag] == 0) {
				dissolved_tags[loc_tag] = pre_tag;
			}
		}

        // ��ʱ���ж���Ϊ0���������ж��ٸ����ڵ�
        // ��һ��ѭ�����ҳ��ж��ٸ����ڵ㣬�ֱ���

        for (uint i = 1; i < tuple_tag; i++) {

            if (dissolved_tags[i] == 0) {
                solved_tags[i] = ++root_num;
            }
        }

        // �ٽ���һ��ѭ����Ϊÿһ����㸳���ֵ
        //unsigned int temp_tag_idx;
        for (uint i = 1; i < tuple_tag;i++) {

            // ��Ϊÿһ���ȼ��б���С�������ǰ��
            // ���Դ�ǰ����ֵֻ��Ҫ��ǰһ����ֵ����

            if (solved_tags[i] == 0) {
                solved_tags[i] = solved_tags[dissolved_tags[i]];
            }
        }

        // �����ؽ����ֵ
        uint dump_num = 0;
        for (int i = 0; i < rows; i++) {

            dump_num = tuple_list[i].length;
            for (uint j = 0; j < dump_num; j++) {

                start_idx = tuple_list[i].List[j].s_cidx;
                end_idx = tuple_list[i].List[j].e_cidx;
                temp_tag = solved_tags[tuple_list[i].List[j].tag_idx];

                for (uint m = start_idx; m < end_idx + 1; m++) {

                    idx = cols64 * i + m;
                    result[idx] = temp_tag;
                } // ����һ���е�һ����ͨ�ŵĸ�ֵ
            } // ����һ�еĸ�ֵ
        } // �������еĸ�ֵ

        free(dissolved_tags);
        free(solved_tags);
    }

    // ���û����ͨ������, ֱ�ӷ���0

    for (int i = 0; i < rows; i++) {
        free(tuple_list[i].List);
        tuple_list[i].List = NULL;
    }
    free(tuple_list);
    free(ecList->List);
    free(ecList);

    *label_num = root_num;
    return result;

}


void check_rList_alloc(tuple_row* rList) {

    // �ж��Ƿ���Ҫ���·����ڴ�
    if (rList->length == rList->alloc_length) {

        uint new_size = rList->alloc_length + TUPLE_SIZE;
        con_tuple* tem_p = (con_tuple*)realloc(rList->List, new_size * sizeof(con_tuple));
        if (tem_p == NULL) {
            fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
            exit(-1);
        }
        else {
            rList->List = tem_p;
            rList->alloc_length = new_size;
        }

    }
}


unsigned int get_tag(tuple_row* rList, unsigned int start_idx, unsigned int end_idx, equ_couple_list* ecList) {

    uint tag_return = 0;
    uint dump_num = rList->length;
    if (dump_num == 0) {
        return tag_return;
    }
    else {

        int flag_overlap = 0;
        uint left_edge = 0, right_edge = 0;

        // ������ſ�,�Ƿ�����һ�е������ſ�,����ֱ���������ص��Ĳ���

        for (uint i = 0; i < dump_num; i++) {

            left_edge = rList->List[i].s_cidx;
            right_edge = rList->List[i].e_cidx;

            // ����ص���
            if (line_intersection(left_edge, right_edge, start_idx, end_idx)) {
                // �Ѿ����ص��Ĳ��֣���¼�ȼ۶ԣ�������б��
                if (flag_overlap) {
                    add_ec(ecList, tag_return, rList->List[i].tag_idx);
                }
                // ��һ���ص������б�ǣ�����¼�ȼ۶�
                else {
                    tag_return = rList->List[i].tag_idx;
                    flag_overlap = 1;
                }
            }
        }
    }

    // ���û���ص��Ĳ���,�򷵻�0����ζ�ų������µĶ����ſ飬tuple_tag��Ҫ��������������
    return tag_return;
}


int line_intersection(unsigned int a1, unsigned int a2, unsigned int b1, unsigned int b2) {

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


void add_ec(equ_couple_list* ecList, unsigned int tag_a, unsigned int tag_b) {

    if (tag_a == tag_b) {
        // ���ֵ��ͬ�������¼�ȼ۶�
    }
    else {
        // ���ֵ��ͬ����¼�ȼ۶�

        // ���ж��Ƿ���Ҫ���·����ڴ�
        if (ecList->length == ecList->alloc_length) {
            uint new_size = ecList->alloc_length + EC_SIZE;
            equ_couple* tem_p = (equ_couple*)realloc(ecList->List, new_size * sizeof(equ_couple));
            if (tem_p == NULL) {
                fprintf(stderr, "memory allocation failed in %s at line %d!\r\n", __FILE__, __LINE__);
                exit(-1);
            }
            else {
                ecList->List = tem_p;
                ecList->alloc_length = new_size;
            }
        }

        // �ж��ĸ�tagֵ����
        if (tag_a < tag_b) {
            ecList->List[ecList->length].min_tag = tag_a;
            ecList->List[ecList->length].max_tag = tag_b;
            ecList->length++;
        }
        else {
            ecList->List[ecList->length].min_tag = tag_b;
            ecList->List[ecList->length].max_tag = tag_a;
            ecList->length++;
        }

    }

}


unsigned int min_uint(unsigned int a, unsigned int b) {
    return a < b ? a : b;
}

unsigned int max_uint(unsigned int a, unsigned int b) {
    return a > b ? a : b;
}



