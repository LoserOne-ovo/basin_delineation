import os
import sys
import gc
import sqlite3
import math
import time
import numpy as np
import argparse
sys.path.append("../")
import db_op as dp
import file_op as fp
from util import interface as cfunc
from util import raster
from rtree import index
from numba import jit


"""
    脚本预期接受两个参数：
        1. 工程配置配置文件
        2. 第一级流域的类型，暂时只支持 type=4
"""
"""
    type = 4
      step 1: 区分大陆海岸线和岛屿海岸线
      step 2: 统计大陆海岸线上的所有河流入海口（汇流累积量大于河网阈值）
      step 3: 计算所有岛屿的相关属性
      step 4: 计算所有内流区终点的相关属性
"""


def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="create property database for a basin at level 1.")
    parser.add_argument("config", help="configuration file")
    parser.add_argument("top_code", help="code of level 1 basin")
    args = parser.parse_args()

    ini_file = args.config
    if not os.path.isfile(ini_file):
        raise RuntimeError("Configuration file does not exist!")

    # 配置文件中要读取三个参数
    tgt_args = ["project_root", "level_database", "minimum_river_threshold"]
    ini_dict = {}
    with open(ini_file, "r") as fs:
        line = fs.readline()
        while line:
            line_str = line.split("=")
            if line_str[0] in tgt_args:
                ini_dict[line_str[0]] = line_str[1]
            line = fs.readline()
    fs.close()

    flag = True
    # 检查项目根目录参数
    if tgt_args[0] in ini_dict.keys():
        p_root = ini_dict[tgt_args[0]].strip()
        if not os.path.exists(p_root):
            print("The path of %s does not exist!" % tgt_args[0])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[0])
        flag = False
    # 检查汇总数据库参数
    if tgt_args[1] in ini_dict.keys():
        level_db = ini_dict[tgt_args[1]].strip()
        if not os.path.isfile(level_db):
            print("The path of %s does not exist!" % tgt_args[1])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[1])
        flag = False
    # 检查河网阈值
    if tgt_args[2] in ini_dict.keys():
        min_ths = ini_dict[tgt_args[2]].strip()
        if not check_float(min_ths):
            print("%s could not be converted to a float!" % tgt_args[2])
            flag = False
        else:
            min_ths = float(min_ths)
            if min_ths <= 0.:
                print("%s must be larger than 0!" % tgt_args[2])
                flag = False
    else:
        print("%s not found in the config file!" % tgt_args[2])
        flag = False

    # 1级流域编码在1~9之间
    t_code = args.top_code
    if top_code not in [str(i) for i in range(1, 10)]:
        print("The code of level 1 basin is invalid!")
        flag = False

    if flag is False:
        exit(-1)

    return p_root, level_db, min_ths, t_code


def check_float(num_str):
    """
    check whether the input string could be converted to a float
    :param num_str:
    :return:
    """
    try:
        float(num_str)
        return True
    except:
        return False


@jit(nopython=True)
def distance_2d(cor_a, cor_b):
    """
    Calculate the distance between two points on a two-dimensional plane
    :param cor_a: point a
    :param cor_b: point b
    :return: distance
    """
    a2 = math.pow(cor_a[0] - cor_b[0], 2)
    b2 = math.pow(cor_a[1] - cor_b[1], 2)
    return math.sqrt(a2 + b2)


@jit(nopython=True)
def check_island_sink(row, col, envelopes, num):
    """
    Determine whether the sink bottom is in the envelope of some island
    :param row: row index of the sink bottom
    :param col: col index of the sink bottom
    :param envelopes: envelopes of islands
    :param num: the number of islands which have the sink bottom in their envelopes
    :return:
    """
    count = 0
    island_id = -1
    for i in range(num):
        min_row, min_col, max_row, max_col = envelopes[i]
        if min_row < row < max_row and min_col < col < max_col:
            count += 1
            island_id = i

    return count, island_id


@jit(nopython=True)
def calc_island_radius(area, cell_area):
    """
    估算岛屿的半径
    :param area: 岛屿面积
    :param cell_area: 单个栅格的面积
    :return:
    """
    return math.sqrt(area / (cell_area * math.pi))


# 默认第一层级是大陆和岛屿的混合， 对应type=4
def basin_preprocess_4(root, min_river_ths, level_db, code):
    """
    对 type=4 的第一层级流域进行处理，计算相关属性，
    使之能按照流域划分方法，被划分为若干个子流域。
    :param root: 项目的根目录
    :param min_river_ths: 河网阈值
    :param level_db: 流域信息汇总数据库
    :param code: 第一层级流域编码
    :return: None
    """
    ############################
    #        读取栅格数据        #
    ############################
    # 获取流域工作路径
    work_folder = fp.get_basin_folder(root, code)
    # 读取tif文件（不包括栅格）
    dir_arr, upa_arr, elv_arr, geo_trans, proj = raster.read_tif_files(work_folder, code, 0)
    ul_lon = geo_trans[0]
    width = geo_trans[1]
    ul_lat = geo_trans[3]
    height = geo_trans[5]
    # 初始化统计参数
    arr_shape = dir_arr.shape
    total_area = 0.0
    out_drainage_area = 0.0
    sb_id = 1
    mo_id = 1
    is_id = 1
    print("Data loaded at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    ############################
    #        创建数据库表        #
    ############################
    # 获取流域工作路径，并在数据库中添加数据表
    db_path = os.path.join(work_folder, str(code) + ".db")
    conn = sqlite3.connect(db_path)
    dp.create_bp_table(conn)
    dp.create_gt_table(conn)
    dp.create_mo_table(conn)
    # 获取数据库连接游标
    cursor = conn.cursor()

    ###############################
    #        计算地理参考属性        #
    ###############################
    ins_val = (geo_trans[0], geo_trans[1], geo_trans[2], geo_trans[3], geo_trans[4], geo_trans[5],
               int(arr_shape[0]), int(arr_shape[1]), 0, 0)
    cursor.execute(dp.gt_sql, ins_val)

    #######################################
    #        区分大陆海岸线和岛屿海岸线        #
    #######################################
    # 提取海陆边界，并做四连通分析
    all_edge = np.zeros(arr_shape, dtype=np.uint8)
    all_edge[dir_arr == 0] = 1
    label_res, label_num = cfunc.label(all_edge)
    # 认为汇流累积量最大值所处的连通部分为大陆边界，其余为岛屿边界
    max_upa_index = np.argmax(upa_arr)
    mainland_label = label_res[np.unravel_index(max_upa_index, arr_shape)]
    mainland_edge = (label_res == mainland_label)
    del label_res
    gc.collect()
    out_drainage_area = np.sum(upa_arr[mainland_edge])
    total_area = out_drainage_area

    ############################################
    #        将大陆海岸线上的所有点插入到R树中       #
    #        同时判断是否为河流入海口              #
    ############################################
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
            cursor.execute(dp.mo_sql, (int(loc_i), int(loc_j), float(temp_area)))
    conn.commit()
    print("Exorheic num: %d" % (mo_id - 1))
    print("Exorheic finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    #############################
    #        标记岛屿的位置        #
    #############################
    # 计算岛屿边界，并回收内存
    island_edge = all_edge ^ mainland_edge
    del all_edge, mainland_edge
    gc.collect()
    # 对岛屿进行四连通域分析，
    island_label_res, island_num = cfunc.label(island_edge)
    print("Island num: %d" % island_num)
    # 调用C，统计岛屿的相关信息
    island_center, island_sample, island_area, island_ref_area, island_envelope = \
        cfunc.island_statistic(island_label_res, island_num, dir_arr, upa_arr)
    if island_num > 0:
        dp.create_is_table(conn)
    # 回收内存
    del island_edge, island_label_res
    gc.collect()

    #########################
    #     计算内流区属性      #
    #########################
    # 找到所有的内流区
    idx_list = np.argwhere(dir_arr == 255)
    if idx_list.shape[0] > 0:
        dp.create_sb_table(conn)
    # 计算每个内流区的属性，并插入到数据库
    for loc_i, loc_j in idx_list:
        sink_type = 1
        sb_lon = ul_lon + (loc_j + 0.5) * width
        sb_lat = ul_lat + (loc_i + 0.5) * height
        sample_i = 0
        sample_j = 0
        sink_area = upa_arr[loc_i, loc_j]
        # 判断内流区是否在岛屿上
        temp_count, temp_id = check_island_sink(loc_i, loc_j, island_envelope, island_num)
        # 如果在大陆上
        if temp_count == 0:
            total_area += sink_area
        # 如果在岛屿上
        elif temp_count == 1:
            sink_type = 2
            island_area[temp_id] += sink_area
            sample_i, sample_j = island_sample[temp_id]
        # 如果不能判断在哪个岛屿，抛出错误
        else:
            conn.commit()
            conn.close()
            raise RuntimeError("unable to locate a sink into a specific island.")

        ins_val = (sb_id, int(loc_i), int(loc_j), sb_lon, sb_lat, float(sink_area),
                   int(sample_i), int(sample_j), sink_type)
        cursor.execute(dp.sb_sql, ins_val)
        sb_id += 1
    conn.commit()
    print("Endorheic num: %d" % (sb_id - 1))
    print("Endorheic finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    #########################
    #     计算岛屿的属性      #
    #########################
    # 计算离岛屿外包矩形中心最近的大陆像元,以及两者之间的距离
    for i in range(island_num):
        center_i, center_j = island_center[i]
        sample_i, sample_j = island_sample[i]
        radius = calc_island_radius(island_area[i], island_ref_area[i])
        total_area += island_area[i]
        min_row, min_col, max_row, max_col = island_envelope[i]
        gc_cor = (center_j, center_j, center_i, center_i)
        nearest_j, nearest_i = list(sp_idx.nearest(gc_cor, objects="raw"))[0]
        nearest_dst = distance_2d((center_j, center_i), (nearest_j, nearest_i)) - radius
        is_type = 1 if nearest_dst < 10 and island_area[i] < 0.1 else 2
        ins_val = (is_id, float(center_i), float(center_j), int(sample_i), int(sample_j), float(radius),
                   float(island_area[i]), float(island_ref_area[i]), int(min_row), int(min_col), int(max_row),
                   int(max_col),
                   float(nearest_dst), int(nearest_i), int(nearest_j), is_type)
        cursor.execute(dp.is_sql, ins_val)
        is_id += 1
    conn.commit()
    print("Island finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    ############################
    #        统计流域属性        #
    ############################
    ins_val = (4, float(out_drainage_area), float(total_area), None, None, None, None, sb_id - 1, is_id - 1)
    cursor.execute(dp.bp_sql, ins_val)
    conn.commit()
    conn.close()

    ###############################
    #        统计流域汇总属性        #
    ###############################
    ins_val = (code, 4, float(total_area), float(total_area), sb_id - 1, is_id - 1, 1)
    dp.insert_basin_stat(level_db, 1, ins_val)


if __name__ == "__main__":
    
    time_start = time.time()
    print("Mission started at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_start)))

    # 解析参数
    project_root, level_database, minimum_river_threshold, top_code = create_args()
    # 业务函数
    basin_preprocess_4(project_root, level_database, minimum_river_threshold, top_code)

    time_end = time.time()
    time_consumption = time_end - time_start
    print("Mission finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_end)))
    print("Total time consumption: %.2f " % time_consumption)
