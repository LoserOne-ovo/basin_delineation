import sys
sys.path.append("../")
from file_op import get_basin_folder
from db_op import *
from interface import label, island_statistic
from util.raster import read_tif_files
import numpy as np
from rtree import index
from numba import jit
import gc
import sqlite3
import math
import time


"""
    总体上分成N个部分：
      1. 大陆边界
      
      2. 岛屿
      
      3. 内流区

"""


@jit(nopython=True)
def distance_2d(cor_a, cor_b):

    a2 = math.pow(cor_a[0] - cor_b[0], 2)
    b2 = math.pow(cor_a[1] - cor_b[1], 2)
    return math.sqrt(a2 + b2)


@jit(nopython=True)
def check_island_sink(row, col, envelopes, num):

    count = 0
    island_id = -1
    for i in range(num):
        min_row, min_col, max_row, max_col = envelopes[i]
        if min_row < row < max_row and min_col < col < max_col:
            count += 1
            island_id = i

    return count, island_id


# 默认第一层级是大陆和岛屿的混合， 对应type=4
def basin_preprocess(root, code, min_river_ths, stat_db, stat_sql, basin_type=4, p_level=1, ul_offset=(0, 0)):

    # 获取流域工作路径，并在数据库中添加数据表
    work_folder = get_basin_folder(root, code)
    db_path = work_folder + r"\%s.db" % code
    conn = sqlite3.connect(db_path)
    create_bp_table(conn)
    create_gt_table(conn)
    create_mo_table(conn)

    # 读取tif文件
    dir_arr, upa_arr, elv_arr, geo_trans, proj = read_tif_files(work_folder, code, 0)
    ul_lon = geo_trans[0]
    width = geo_trans[1]
    ul_lat = geo_trans[3]
    height = geo_trans[5]

    # 初始化一些参数
    arr_shape = dir_arr.shape
    print(arr_shape)
    total_area = 0.0
    out_drainage_area = 0.0
    sb_id = 1
    mo_id = 1
    is_id = 1

    # 获取数据库连接游标
    cursor = conn.cursor()

    print("Data loaded at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    ###############################
    #        计算地理参考属性        #
    ###############################
    ins_val = (geo_trans[0], geo_trans[1], geo_trans[2], geo_trans[3], geo_trans[4], geo_trans[5],
               int(arr_shape[0]), int(arr_shape[1]), ul_offset[0], ul_offset[1])
    cursor.execute(gt_sql, ins_val)


    ############################################
    #        计算大陆边界上的主要外流区的属性        #
    ############################################

    # 提取海陆边界，并做四连通分析
    all_edge = np.zeros(arr_shape, dtype=np.uint8)
    all_edge[dir_arr == 0] = 1
    label_res, label_num = label(all_edge)

    # 认为汇流累积量最大值所处的连通部分为大陆边界，其余为岛屿边界
    max_upa_index = np.argmax(upa_arr)
    mainland_label = label_res[np.unravel_index(max_upa_index, arr_shape)]
    mainland_edge = (label_res == mainland_label)
    del label_res
    gc.collect()
    
    out_drainage_area = np.sum(upa_arr[mainland_edge])
    total_area = out_drainage_area

    sp_idx = index.Index(interleaved=False)
    # 提取大陆边界上的主要外流区
    idx_list = np.argwhere(mainland_edge)
    for loc_i, loc_j in idx_list:
        # 插入到R树中
        cor = (loc_j + 0.5, loc_j + 0.5, loc_i + 0.5, loc_i + 0.5)
        sp_idx.insert(mo_id, cor, obj=(loc_j, loc_i))
        # 统计面积
        temp_area = upa_arr[loc_i, loc_j]
        if temp_area > min_river_ths:
            # 向数据库中插入该像元信息
            cursor.execute(mo_sql, (int(loc_i), int(loc_j), float(temp_area)))
    conn.commit()

    print("Exorheic num: %d" % (mo_id - 1))
    print("Exorheic finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    # 计算岛屿边界，并回收内存
    island_edge = all_edge ^ mainland_edge
    del all_edge, mainland_edge
    gc.collect()

    #############################
    #        计算岛屿的属性        #
    #############################

    # 计算岛屿信息
    island_label_res, island_num = label(island_edge)
    print("Island num: %d" % island_num)
    island_center, island_sample, island_radius, island_area, island_ref_area, island_envelope = island_statistic(island_label_res, island_num, dir_arr, upa_arr)
    if island_num > 0:
        create_is_table(conn)

    del island_edge, island_label_res
    gc.collect()

    #############################
    #     检查有没有岛屿内流区      #
    #############################
    idx_list = np.argwhere(dir_arr == 255)
    if idx_list.shape[0] > 0:
        create_sb_table(conn)
    for loc_i, loc_j in idx_list:
        sink_type = 1
        sb_lon = ul_lon + (loc_j + 0.5) * width
        sb_lat = ul_lat + (loc_i + 0.5) * height
        sample_i = 0
        sample_j = 0
        temp_area = upa_arr[loc_i, loc_j]
        temp_count, temp_id = check_island_sink(loc_i, loc_j, island_envelope, island_num)
        if temp_count == 0:
            total_area += temp_area
        elif temp_count == 1:
            island_area[temp_id] += temp_area
            sample_i, sample_j = island_sample[temp_id]
        else:
            conn.commit()
            conn.close()
            raise RuntimeError("unable to locate a sink into a specific island.")

        ins_val = (sb_id, int(loc_i), int(loc_j), sb_lon, sb_lat, float(temp_area),
                   int(sample_i), int(sample_j), sink_type)
        cursor.execute(sb_sql, ins_val)
        sb_id += 1
    conn.commit()

    print("Endorheic num: %d" % (sb_id - 1))
    print("Endorheic finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))


    # 计算离岛屿外包矩形中心最近的大陆像元,以及两者之间的距离
    for i in range(island_num):
        center_i, center_j = island_center[i]
        sample_i, sample_j = island_sample[i]
        radius = island_radius[i]
        temp_area = island_area[i]
        total_area += temp_area
        ref_area = island_ref_area[i]
        min_row, min_col, max_row, max_col = island_envelope[i]

        gc_cor = (center_j, center_j, center_i, center_i)
        nearest_j, nearest_i = list(sp_idx.nearest(gc_cor, objects="raw"))[0]
        nearest_dst = distance_2d((center_j, center_i), (nearest_j, nearest_i)) - radius
        is_type = 1 if nearest_dst < 10 and temp_area < 0.1 else 2

        ins_val = (is_id, float(center_i), float(center_j), int(sample_i), int(sample_j), float(radius),
                   float(temp_area),float(ref_area), int(min_row), int(min_col), int(max_row), int(max_col),
                   float(nearest_dst), int(nearest_i), int(nearest_j), is_type)
        cursor.execute(is_sql, ins_val)
        is_id += 1
    conn.commit()

    print("Island finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))


    ###############################
    #        统计流域总的属性        #
    ###############################

    ins_val = (basin_type, float(out_drainage_area), float(total_area), None, None, None, None, sb_id - 1, is_id - 1)
    cursor.execute(bp_sql, ins_val)
    conn.commit()
    conn.close()


    ###############################
    #        统计流域汇总属性        #
    ###############################

    conn = sqlite3.connect(stat_db)
    cursor = conn.cursor()
    ins_val = (code, basin_type, float(total_area), float(total_area), sb_id - 1, is_id - 1, 1)
    cursor.execute(stat_sql, ins_val)
    conn.commit()
    conn.close()



if __name__ == "__main__":

    time_start = time.time()
    print("Mission started at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_start)))

    project_root = r"E:\qyf\data\Australia"
    project_code = "7"
    min_river_threshold = 10

    level = 1
    level_table = "level_%s" % str(level)
    stat_db_path = r"E:\qyf\data\Australia\statistic.db"
    create_stat_table(stat_db_path, level_table)
    statistic_sql = "INSERT INTO %s VALUES(?, ?, ?, ?, ? , ?, ?)" % level_table

    basin_preprocess(project_root, project_code, min_river_threshold, stat_db_path, statistic_sql)

    time_end = time.time()
    time_consumption = time_end - time_start

    print("Mission finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_end)))
    print("Total time consumption: %.2f " % time_consumption)











