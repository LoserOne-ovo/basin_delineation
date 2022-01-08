import gc
import os
import sys
import numpy as np
from rtree import index
from db_op import *
from file_op import clone_basin
from interface import *
sys.path.append("..")
from util.raster import read_tif_files, array2tif, raster2shp_mem
from numba import jit
import time



def divide_basin_1or2(folder, code, bas_type, sink_num, threshold, stat_db_path, sql_statement):
    """

    :param folder:
    :param code:
    :param bas_type:
    :param sink_num:
    :param threshold:
    :param stat_db_path:
    :param sql_statement:
    :return:
    """

    # 读取流域出口信息、流域面积信息和内流区信息
    db_path = os.path.join(folder, code + '.db')
    outlet_idx, area, sinks = get_outlet_1(db_path, sink_num)
    ul_offset = get_ul_offset(db_path)

    # 读取栅格数据
    dir_arr, upa_arr, elv_arr, geotransform, proj = read_tif_files(folder, code, sink_num)

    # 流域划分
    basin, sub_num, b_types, b_areas, b_outlets, b_envelopes, sink_merge_flag, other_sinks = \
        divide_1or2(outlet_idx, bas_type, dir_arr, upa_arr, elv_arr, threshold, area, sinks, sink_num)

    # 分割流域，并保存为新的输入
    result = break_into_sub_basins(basin, dir_arr, upa_arr, elv_arr, sub_num, b_types, b_areas, b_outlets, b_envelopes,
                          None, None, sink_merge_flag, other_sinks, None, None, None, None, None, None,
                          ul_offset, geotransform, proj, threshold, code, folder, stat_db_path, sql_statement)

    return result


def divide_1or2(outlet_idx, bas_type, dir_arr, upa_arr, elv_arr, threshold, area, sinks, sinks_num):
    """

    :param outlet_idx:
    :param bas_type:
    :param dir_arr:
    :param upa_arr:
    :param elv_arr:
    :param threshold:
    :param area:
    :param sinks:
    :param sinks_num:
    :return:
    """

    # 建立流域出水口数组
    sub_outlet_idxs = np.zeros((11, 2), dtype=np.int32)
    # 建立流域类型列表
    btype_list = np.zeros((11,), dtype=np.uint8)
    # 建立流域面积列表
    barea_list = np.zeros((11,), dtype=np.float64)
    # 流域envelope矩阵
    rows, cols = dir_arr.shape
    envelopes = np.zeros((11, 4), dtype=np.int32)
    envelopes[:, 0] = rows
    envelopes[:, 1] = cols
    # 子流域编码结果
    basin = np.zeros((rows, cols), dtype=np.uint8)

    # 计算逆d8流向
    re_dir_arr = calc_reverse_dir(dir_arr)
    # pfafstetter编码划分子流域
    sub_num = pfafstetter(outlet_idx, basin, re_dir_arr, upa_arr, sub_outlet_idxs, threshold)
    # 设置流域类型列表，奇数编号（索引为偶数）为有上游的外流区，偶数标号（索引为奇数）为无上游的外流区
    btype_list[1] = 2
    for i in range(2, sub_num + 1, 2):
        btype_list[i] = 1
        btype_list[i + 1] = 2
    # 判断最后一个流域的类型
    if bas_type != 2:
        btype_list[sub_num] = 1

    # 出水口的汇流累积量
    outlet_idx_area = upa_arr[outlet_idx]
    # 上游来水量
    upper_area = outlet_idx_area - area
    # 各个子流域的面积
    for i in range(sub_num, 1, -2):
        # 设置有上游区子流域的面积
        barea_list[i] = upa_arr[sub_outlet_idxs[i, 0], sub_outlet_idxs[i, 1]] - upper_area
        # 设置无上游区子流域的面积
        barea_list[i - 1] = upa_arr[sub_outlet_idxs[i - 1, 0], sub_outlet_idxs[i - 1, 1]]
        # 更新上游来水区面积
        upper_area += barea_list[i] + barea_list[i - 1]
    barea_list[1] = upa_arr[sub_outlet_idxs[1, 0], sub_outlet_idxs[1, 1]] - upper_area

    # 一个层级可以编码1~10共10个子流域，而流域划分最多编码到9，剩下的编码位置可以用完整的内流区补足
    sink_probe = 0
    # 参与编码的内流区
    while sink_probe < sinks_num and sub_num < 10:
        sub_num += 1
        sub_outlet_idxs[sub_num, 0] = sinks[sink_probe][1]
        sub_outlet_idxs[sub_num, 1] = sinks[sink_probe][2]
        barea_list[sub_num] = sinks[sink_probe][5]
        btype_list[sub_num] = 3
        sink_probe += 1

    # 其余的未编码内流区
    other_sink_num = sinks_num - sink_probe
    if other_sink_num > 0:
        other_sinks = sinks[sink_probe:]
    else:
        other_sinks = None

    # 判断是否有内流区需要编码
    main_sink_num = sink_probe
    if main_sink_num > 0:
        main_sink_idxs = np.zeros((main_sink_num,), dtype=np.uint64)
        for i in range(main_sink_num):
            main_sink_idxs[i] = sinks[i][1] * cols + sinks[i][2]
        colors = np.arange(sub_num + 1 - main_sink_num, sub_num + 1, 1, dtype=np.uint8)
        paint_up_uint8(main_sink_idxs, colors, re_dir_arr, basin)

    # 判断是否其他无法编码的外流区要合并
    if other_sink_num > 0:
        other_sink_idxs = np.zeros((other_sink_num,), dtype=np.uint64)
        for i in range(other_sink_num):
            other_sink_idxs[i] = other_sinks[i][1] * cols + other_sinks[i][2]
        # 内流区数量少于245，使用unsigned char
        if other_sink_num < 245:
            sink_merge_uint8(other_sink_idxs, re_dir_arr, elv_arr, basin)
        # 内流区数量大于245，使用unsigned short
        # 超过65525，则在开始时就抛出错误
        else:
            basin = basin.astype(np.uint16)
            sink_merge_uint16(other_sink_idxs, re_dir_arr, elv_arr, basin)
            basin = basin.astype(np.uint8)

    # 记录内流区的合并情况
    sink_merge_flag = np.zeros((other_sink_num,), dtype=np.uint8)
    for i in range(other_sink_num):
        sink_merge_flag[i] = basin[other_sinks[i][1], other_sinks[i][2]]

    # 计算子流域外包矩形
    get_basin_envelopes(basin, envelopes)

    return basin, sub_num, btype_list, barea_list, sub_outlet_idxs, envelopes, sink_merge_flag, other_sinks


def divide_basin_3(folder, code, bas_type, sink_num, threshold, stat_db_path, sql_statement):
    """

    :param folder:
    :param code:
    :param bas_type:
    :param sink_num:
    :param threshold:
    :param stat_db_path:
    :param sql_statement:
    :return:
    """

    # 读取流域出口信息、流域面积信息和内流区信息
    db_path = os.path.join(folder, code + '.db')
    outlet_idx, area, sinks = get_outlet_1(db_path, sink_num)
    ul_offset = get_ul_offset(db_path)

    # 判断合并到该内流区的其他内流区是否足够大
    critical_area = area / 9
    critical_count = 0
    if sink_num > 0:
        for sink_info in sinks:
            if sink_info[5] > critical_area:
                critical_count += 1
            else:
                break

    # 读取栅格数据
    dir_arr, upa_arr, elv_arr, geotransform, proj = read_tif_files(folder, code, sink_num)

    # 如果足够大的内流区的数量小于2，则把内流区当成一个完整流域处理
    if critical_count < 2:
        basin, sub_num, b_types, b_areas, b_outlets, b_envelopes, sink_merge_flag, other_sinks = \
            divide_1or2(outlet_idx, bas_type, dir_arr, upa_arr, elv_arr, threshold, area, sinks, sink_num)
    # 如果内流区的面积有相仿的，则编码较大的内流区，将其余的内流区合并到已编码的内流区中
    else:
        basin, sub_num, b_types, b_areas, b_outlets, b_envelopes, sink_merge_flag, other_sinks = \
            divide_3(outlet_idx, dir_arr, elv_arr, area, sinks, sink_num, critical_count)

    # 分割流域，并保存为新的输入
    result = break_into_sub_basins(basin, dir_arr, upa_arr, elv_arr, sub_num, b_types, b_areas, b_outlets, b_envelopes,
                          None, None, sink_merge_flag, other_sinks, None, None, None, None, None, None,
                          ul_offset, geotransform, proj, threshold, code, folder, stat_db_path, sql_statement)

    return result


def divide_3(outlet_idx, dir_arr, elv_arr, area, sinks, sinks_num, depart_num):
    """

    :param outlet_idx:
    :param dir_arr:
    :param elv_arr:
    :param area:
    :param sinks:
    :param sinks_num:
    :param depart_num:
    :return:
    """

    # 建立流域出水口数组
    sub_outlet_idxs = np.zeros((11, 2), dtype=np.int32)
    # 建立流域类型列表
    btype_list = np.zeros((11,), dtype=np.uint8)
    # 建立流域面积列表
    barea_list = np.zeros((11,), dtype=np.float64)
    # 流域envelope矩阵
    rows, cols = dir_arr.shape
    envelopes = np.zeros((11, 4), dtype=np.int32)
    envelopes[:, 0] = rows
    envelopes[:, 1] = cols
    # 子流域编码结果
    basin = np.zeros((rows, cols), dtype=np.uint8)

    # 辅助参数
    sub_num = 1
    sink_probe = 0

    # 第一个流域
    sub_outlet_idxs[1, 0] = outlet_idx[0]
    sub_outlet_idxs[1, 1] = outlet_idx[1]
    barea_list[1] = area
    btype_list[1] = 3

    # 其余的编码内流区
    while sink_probe < depart_num and sub_num < 10:
        sub_num += 1
        sub_outlet_idxs[sub_num, 0] = sinks[sink_probe][1]
        sub_outlet_idxs[sub_num, 1] = sinks[sink_probe][2]
        barea_list[sub_num] = sinks[sink_probe][5]
        btype_list[sub_num] = 3
        sink_probe += 1

    # 其余的未编码内流区
    other_sink_num = sinks_num - sink_probe
    if other_sink_num > 0:
        other_sinks = sinks[sink_probe:]
    else:
        other_sinks = None

    # 计算逆流向和初始化流域划分结果
    re_dir_arr = calc_reverse_dir(dir_arr)
    basin = np.zeros(dir_arr.shape, dtype=np.uint8)

    # 为参与编码的内流区上色
    coded_sink_idxs = np.zeros((sub_num,), dtype=np.uint64)
    for i in range(1, sub_num + 1):
        coded_sink_idxs[i - 1] = sub_outlet_idxs[i, 0] * cols + sub_outlet_idxs[i, 1]
    colors = np.arange(1, sub_num + 1, 1, dtype=np.uint8)
    paint_up_uint8(coded_sink_idxs, colors, re_dir_arr, basin)

    # 判断是否其他无法编码的外流区要合并
    if other_sink_num > 0:
        other_sink_idxs = np.zeros((other_sink_num,), dtype=np.uint64)
        for i in range(other_sink_num):
            other_sink_idxs[i] = other_sinks[i][1] * cols + other_sinks[i][2]
        # 内流区数量少于245，使用unsigned char
        if other_sink_num < 245:
            sink_merge_uint8(other_sink_idxs, re_dir_arr, elv_arr, basin)
        # 内流区数量大于245，使用unsigned short
        # 超过65525，则在开始时就抛出错误
        else:
            basin = basin.astype(np.uint16)
            sink_merge_uint16(other_sink_idxs, re_dir_arr, elv_arr, basin)
            basin = basin.astype(np.uint8)

    # 记录内流区的合并情况
    sink_merge_flag = np.zeros((other_sink_num,), dtype=np.uint8)
    for i in range(other_sink_num):
        sink_merge_flag[i] = basin[other_sinks[i][1], other_sinks[i][2]]

    # 计算子流域外包矩形
    get_basin_envelopes(basin, envelopes)
    
    return basin, sub_num, btype_list, barea_list, sub_outlet_idxs, envelopes, sink_merge_flag, other_sinks


def divide_basin_4(folder, code, sink_num, island_num, threshold, stat_db_path, sql_statement):
    """

    :param folder:
    :param code:
    :param sink_num:
    :param island_num:
    :param threshold:
    :param stat_db_path:
    :param sql_statement:
    :return:
    """

    db_path = folder + r"\%s.db" % code
    # 读取流域出口信息、流域面积信息和内流区信息
    outlets, outlet_num, sinks, sink_num, islands, island_num, m_islands, m_island_num, i_sinks, i_sink_num = \
        get_outlet_4(db_path, sink_num, island_num)
    ul_offset = get_ul_offset(db_path)

    # 读取栅格数据
    dir_arr, upa_arr, elv_arr, geotransform, proj = read_tif_files(folder, code, sink_num)
    # 流域划分
    basin, sub_num, b_types, b_areas, b_outlets, b_envelopes, other_outlets, outlet_merge_flag, other_sinks, \
        sink_merge_flag, m_island_merge_flag, island_merge_flag, i_sink_merge_flag = \
        divide_4(outlets, outlet_num, sinks, sink_num, m_islands, m_island_num, islands,
                 island_num, i_sinks, i_sink_num, threshold, dir_arr, upa_arr, elv_arr)
    # 裁剪流域
    result = break_into_sub_basins(basin, dir_arr, upa_arr, elv_arr, sub_num, b_types, b_areas, b_outlets, b_envelopes,
                          outlet_merge_flag, other_outlets, sink_merge_flag, other_sinks, i_sink_merge_flag, i_sinks, island_merge_flag, islands,
                          m_island_merge_flag, m_islands, ul_offset, geotransform, proj, threshold,
                          code, folder, stat_db_path, sql_statement)

    return result


def divide_4(outlets, outlet_num, sinks, sink_num, m_islands, m_island_num, islands, island_num, i_sinks, i_sink_num, min_threshold,
             dir_arr, upa_arr, elv_arr):
    """

    :param outlets:
    :param outlet_num:
    :param sinks:
    :param sink_num:
    :param m_islands:
    :param m_island_num:
    :param islands:
    :param island_num:
    :param i_sinks:
    :param i_sink_num:
    :param dir_arr:
    :param upa_arr:
    :param elv_arr:
    :return:
    """
    #########################################
    #               参数初始化                #
    #########################################

    # 二维数组大小
    arr_shape = dir_arr.shape
    # 建立流域出水口数组
    sub_outlet_idxs = np.zeros((11, 2), dtype=np.int32)
    # 建立流域类型数组
    btype_list = np.zeros((11,), dtype=np.uint8)
    # 建立流域面积数组
    barea_list = np.zeros((11,), dtype=np.float64)
    # 流域envelope矩阵
    rows, cols = arr_shape
    envelopes = np.zeros((11, 4), dtype=np.int32)
    envelopes[:, 0] = rows
    envelopes[:, 1] = cols
    # 初始化流域划分结果矩阵
    basin = np.zeros(arr_shape, dtype=np.uint8)
    # 编码数
    code_idx = 1

    #########################################
    #                尝试编码                #
    #########################################
    # 按照面积大小，取外流区出水口，内流区和岛屿，尝试组成编码
    di_outlet_num, di_sink_num, di_island_num = att_coding(outlets, outlet_num, sinks, sink_num, islands, island_num)

    #########################################
    #            编码大陆外流流域              #
    #########################################

    # 提取所有海陆边界
    all_edge = np.zeros(arr_shape, dtype=np.uint8)
    all_edge[dir_arr == 0] = 1
    # 对海陆边界进行四连通域分析
    label_res, label_num = label(all_edge)
    # 提取大陆边界对应的编码
    mainland_label = label_res[outlets[0][0], outlets[0][1]]
    # 建立大陆边界二值图像
    mainland_edge = np.zeros(arr_shape, dtype=np.uint8)
    mainland_edge[label_res == mainland_label] = 1

    # 在主要外流出水口出打断大陆边界
    for i in range(di_outlet_num):
        outlet_ridx = outlets[i][0]
        outlet_cidx = outlets[i][1]
        mainland_edge[outlet_ridx, outlet_cidx] = 0


    # 对打断后的大陆边界进行四连通域分析
    mainland_label_res, mainland_label_num = label(mainland_edge)
    temp_coded_num = di_outlet_num + mainland_label_num + di_sink_num + di_island_num
    island_edge = all_edge ^ mainland_edge
    del all_edge, mainland_edge
    gc.collect()
    

    # 标记其余大陆外流出水口到流域图层，并更新流域信息
    basin += mainland_label_res.astype(np.uint8)
    for i in range(mainland_label_num):
        btype_list[code_idx] = 4
        barea_list[code_idx] = np.sum(upa_arr[mainland_label_res == code_idx])
        code_idx += 1
    del mainland_label_res
    gc.collect()
    
    # 将主要流域出水口标记到流域图层以及记录相关信息
    for i in range(di_outlet_num):
        outlet_ridx = outlets[i][0]
        outlet_cidx = outlets[i][1]
        basin[outlet_ridx, outlet_cidx] = code_idx
        btype_list[code_idx] = 1
        barea_list[code_idx] = upa_arr[outlet_ridx, outlet_cidx]
        sub_outlet_idxs[code_idx][0] = outlet_ridx
        sub_outlet_idxs[code_idx][1] = outlet_cidx
        code_idx += 1

    other_outlet_num = outlet_num - di_outlet_num
    if other_outlet_num > 0:
        other_outlets = outlets[di_outlet_num:]
    else:
        other_outlets = None
    outlet_merge_flag = np.zeros((other_outlet_num, ), dtype=np.uint8)
    for i in range(other_outlet_num):
        outlet_merge_flag[i] = basin[other_outlets[i][0], other_outlets[i][1]] 
 
 
    #########################################
    #                补充编码                #
    #########################################

    # 补充编码的阈值是最小外流区的1/3
    sup_area_ths = outlets[di_outlet_num - 1][2] / 3
    sup_coding(temp_coded_num, sup_area_ths, sinks, di_sink_num, sink_num, islands, di_island_num, island_num)

    # 标记主要内流区，并记录相关信息
    for i in range(di_sink_num):
        outlet_ridx = sinks[i][1]
        outlet_cidx = sinks[i][2]
        basin[outlet_ridx, outlet_cidx] = code_idx
        btype_list[code_idx] = 3
        barea_list[code_idx] = sinks[i][5]
        sub_outlet_idxs[code_idx, 0] = outlet_ridx
        sub_outlet_idxs[code_idx, 1] = outlet_cidx
        code_idx += 1

    #########################################
    #        对大陆部分的流域进行流域追踪        #
    #########################################
    re_dir_arr = calc_reverse_dir(dir_arr)
    # 先追踪已编码流域的范围
    outlet_idxs = np.argwhere(basin != 0)
    paint_up_mosaiced_uint8(outlet_idxs, re_dir_arr, basin)


    # 再将剩余的内流区合并到编码流域内
    other_sink_num = sink_num - di_sink_num
    if other_sink_num > 0:
        other_sinks = sinks[di_sink_num:]
    else:
        other_sinks = None

    if other_sink_num > 0:
        other_sink_idxs = np.zeros((other_sink_num,), dtype=np.uint64)
        for i in range(other_sink_num):
            other_sink_idxs[i] = other_sinks[i][1] * cols + other_sinks[i][2]
        # 内流区数量少于245，使用unsigned char
        if other_sink_num < 245:
            sink_merge_uint8(other_sink_idxs, re_dir_arr, elv_arr, basin)
        # 内流区数量大于245，使用unsigned short
        # 超过65525，则在开始时就抛出错误
        else:
            basin = basin.astype(np.uint16)
            sink_merge_uint16(other_sink_idxs, re_dir_arr, elv_arr, basin)
            basin = basin.astype(np.uint8)

    # 记录大陆内流区的合并情况
    sink_merge_flag = np.zeros((other_sink_num,), dtype=np.uint8)
    for i in range(other_sink_num):
        sink_merge_flag[i] = basin[other_sinks[i][1], other_sinks[i][2]]

    ####################################
    #            岛屿补充编码            #
    ####################################

    island_merge_flag = np.zeros((island_num,), dtype=np.uint8)
    frac = 0.02
    ref_cell_area = 0.0081 if island_num <= 0 else islands[0][7]
    size_change_threshold = max(rows * cols * frac, min_threshold / ref_cell_area)
    
    coded_islands_id = []

    # 提取大陆流域的外包矩形
    get_basin_envelopes(basin, envelopes)
    # 已编码的岛屿，记录外包矩形范围，并标记
    for i in range(di_island_num):
        envelopes[code_idx, 0] = islands[i][8]
        envelopes[code_idx, 1] = islands[i][9]
        envelopes[code_idx, 2] = islands[i][10]
        envelopes[code_idx, 3] = islands[i][11]
        island_merge_flag[i] = code_idx
        btype_list[code_idx] = 5
        code_idx += 1
        coded_islands_id.append(i)

    # 计算所有岛屿对现有编码流域外包矩形的改变
    change_env = np.zeros((island_num, 11), dtype=np.int64)
    for i in range(island_num):
        for j in range(1, code_idx):
            change_env[i, j] = calc_enve_change(envelopes[j], islands[i][8:12])

    # 岛屿补充编码
    while code_idx < 11 and di_island_num < island_num:
        # 计算对流域范围改变最大的岛屿集合
        min_changes = np.min(change_env[:, 1:code_idx], axis=1)
        max_change_island = np.argmax(min_changes)
        max_change_size = min_changes[max_change_island]
        # 如果岛屿集合改变流域外包矩形尺寸过大，则将这个岛屿集合单独编码
        if max_change_size > size_change_threshold:
            btype_list[code_idx] = 5
            temp_envelope = islands[max_change_island][8:12]
            envelopes[code_idx] = temp_envelope
            # 并更新差异矩阵
            for i in range(island_num):
                change_env[i, code_idx] = calc_enve_change(temp_envelope, islands[i][8:12])
            coded_islands_id.append(max_change_island)
            island_merge_flag[max_change_island] = code_idx
            code_idx += 1
            di_island_num += 1
        else:
            break

    # 将岛屿分配到最近的编码流域
    island_merge(islands, island_num, island_merge_flag, coded_islands_id, di_island_num, basin)
    island_label_res, t_island_num = label(island_edge)
    island_paint_flag = np.zeros((t_island_num + 1,), dtype=np.uint32)
    m_island_merge_flag = np.zeros((m_island_num,), dtype=np.uint8)

    """建立岛屿四连通编码和岛屿分配流域编码之前的映射关系，并更新相关信息"""
    # 大陆岛屿
    for i in range(m_island_num):
        merge_basin_code = basin[m_islands[i][13:15]]
        island_paint_flag[island_label_res[m_islands[i][3:5]]] = merge_basin_code
        m_island_merge_flag[i] = merge_basin_code
        update_envelope(envelopes[merge_basin_code], m_islands[i][8:12])  # 更新流域外包矩形
    # 岛屿
    for i in range(island_num):
        island_paint_flag[island_label_res[islands[i][3:5]]] = island_merge_flag[i]  # 岛屿四连通编码和流域编码的映射关系
        update_envelope(envelopes[island_merge_flag[i]], islands[i][8:12])  # 更新流域外包矩形

    # 更新岛屿边界编码
    update_island_label(island_label_res, island_paint_flag, t_island_num)
    island_label_res = island_label_res.astype(np.uint8)

    i_sink_merge_flag = np.zeros((i_sink_num,), dtype=np.uint8)
    # 标记岛屿内流区，并更新相关信息
    for i in range(i_sink_num):
        merge_basin_code = island_label_res[i_sinks[i][6:8]]
        island_label_res[i_sinks[i][1:3]] = merge_basin_code
        i_sink_merge_flag[i] = merge_basin_code

    #########################################
    #      岛屿流域进行追踪,并合并到一个图层      #
    #########################################
    outlet_idxs = np.argwhere(island_label_res != 0)
    paint_up_mosaiced_uint8(outlet_idxs, re_dir_arr, island_label_res)
    basin += island_label_res



    return basin, code_idx - 1, btype_list, barea_list, sub_outlet_idxs, envelopes, other_outlets, outlet_merge_flag, other_sinks, \
        sink_merge_flag, m_island_merge_flag, island_merge_flag, i_sink_merge_flag



def att_coding(outlets, outlet_num, sinks, sink_num, islands, island_num):
    """

    :param outlets:
    :param outlet_num:
    :param sinks:
    :param sink_num:
    :param islands:
    :param island_num:
    :return:
    """

    # 尝试性的进行编码,主要编码部分
    # 如果有内流区或群岛的面积比其中一个入海口的面积大，则取而代之
    di_outlet_num = di_sink_num = di_island_num = 0
    di_outlet_area = di_sink_area = di_island_area = 0.0
    di_num = 0

    # 编码部分
    while di_num < 8 and di_outlet_num < outlet_num:

        if di_outlet_num < outlet_num:
            di_outlet_area = outlets[di_outlet_num][2]
        else:
            di_outlet_area = 0.0
        if di_sink_num < sink_num:
            di_sink_area = sinks[di_sink_num][5]
        else:
            di_sink_area = 0.0
        if di_island_num < island_num:
            di_island_area = islands[di_island_num][6]
        else:
            di_island_area = 0.0

        if di_outlet_area >= di_sink_area and di_outlet_area >= di_island_area:
            di_outlet_num += 1
            di_num += 2
        elif di_sink_area >= di_outlet_area and di_sink_area >= di_island_area:
            di_sink_num += 1
            di_num += 1
        else:
            di_island_num += 1
            di_num += 1

    return di_outlet_num, di_sink_num, di_island_num


def sup_coding(temp_code_num, area_ths, sinks, di_sink_num, sink_num, islands, di_island_num, island_num):


    di_sink_area = di_island_area = 0.0
    while temp_code_num < 10:
        if di_sink_num >= sink_num and di_island_num >= island_num:
            return -1
        else:
            if di_sink_num < sink_num:
                di_sink_area = sinks[di_sink_num][6]
            else:
                di_sink_area = 0.0
            if di_island_num < island_num:
                di_island_area = islands[di_island_num][6]
            else:
                di_island_area = 0.0

            if di_sink_area >= di_island_area and di_sink_area >= area_ths:
                di_sink_num += 1
                temp_code_num += 1
            elif di_island_area > di_sink_area and di_island_area > area_ths:
                di_island_num += 1
                temp_code_num += 1
            else:
                return 0
    return 1


def island_merge(islands, island_num, island_merge_flag, coded_islands, di_island_num, basin_arr):


    # 如果没有编码岛屿，直接赋值到最邻近的大陆流域
    if di_island_num == 0:
        for i in range(island_num):
            island_merge_flag[i] = basin_arr[islands[i][13:15]]

    # 如果有编码岛屿，计算最近的岛屿，并与到大陆的距离相比较
    else:
        max_dst = float(basin_arr.shape[0] + basin_arr.shape[1])
        min_dst_island = island_num


        for i in range(island_num):
            # 如果岛屿没有被编码，逐编码岛屿计算距离，保留最近的编码岛屿
            if island_merge_flag[i] == 0:
                min_dst = max_dst
                for j in coded_islands:
                    h_diff = islands[i][1] - islands[j][1]
                    w_diff = islands[i][2] - islands[j][2]
                    temp_dst = math.sqrt(h_diff * h_diff + w_diff * w_diff) - islands[i][5] - islands[j][5]
                    if temp_dst < min_dst:
                        min_dst = temp_dst
                        min_dst_island = j

                # 如果离大陆更近
                if min_dst > islands[i][12]:
                    island_merge_flag[i] = basin_arr[islands[i][13:15]]
                # 如果离岛屿更近
                else:
                    island_merge_flag[i] = island_merge_flag[min_dst_island]

    return 1


@jit(nopython=True)
def calc_enve_change(enve_a, enve_b):

    src_h = enve_a[2] - enve_a[0]
    src_w = enve_a[3] - enve_a[1]
    afc_h = max(enve_a[2], enve_b[2]) - min(enve_a[0], enve_b[0])
    afc_w = max(enve_a[3], enve_b[3]) - min(enve_a[1], enve_b[1])

    return afc_h * afc_w - src_h * src_w


@jit(nopython=True)
def update_envelope(enve_a, enve_b):

    if enve_b[0] < enve_a[0]:
        enve_a[0] = enve_b[0]
    if enve_b[1] < enve_a[1]:
        enve_a[1] = enve_b[1]
    if enve_b[2] > enve_a[2]:
        enve_a[2] = enve_b[2]
    if enve_b[3] > enve_a[3]:
        enve_a[3] = enve_b[3]

    return 1


def divide_basin_5(folder, code, sink_num, island_num, threshold, stat_db_path, sql_statement):


    # 读取流域出口信息、流域面积信息和内流区信息
    db_path = os.path.join(folder, code + '.db')
    total_area, islands, sinks = get_outlet_5(db_path, sink_num)
    ul_offset = get_ul_offset(db_path)

    # 读取栅格数据
    dir_arr, upa_arr, elv_arr, geotransform, proj = read_tif_files(folder, code, sink_num)

    # 判断有没有需要打成大陆看待的大型岛屿
    first_island_area = islands[0][6]
    if (first_island_area > (total_area * 0.7)) and (first_island_area > (3 * threshold)):

        # 预处理
        outlets, outlet_num, m_sinks, m_sink_num, o_islands, o_island_num, m_islands, m_island_num, i_sinks, i_sink_num = \
            prepare_4(dir_arr, upa_arr, islands, island_num, sinks, sink_num, threshold)

        # 如果主岛有两个以上合规的出水口，则当做大陆来处理
        if outlet_num > 2:
            islands = o_islands
            island_num = o_island_num
            basin, sub_num, b_types, b_areas, b_outlets, b_envelopes, other_outlets, outlet_merge_flag, other_sinks, \
                sink_merge_flag, m_island_merge_flag, island_merge_flag, i_sink_merge_flag = \
                divide_4(outlets, outlet_num, m_sinks, m_sink_num, m_islands, m_island_num, islands,
                         island_num, i_sinks, i_sink_num, threshold, dir_arr, upa_arr, elv_arr)

        # 当做岛屿集合来处理
        else:
            m_islands = []
            i_sinks = sinks
            basin, sub_num, b_types, b_areas, b_outlets, b_envelopes, other_outlets, outlet_merge_flag, other_sinks, \
                sink_merge_flag, m_island_merge_flag, island_merge_flag, i_sink_merge_flag = \
                divide_5(islands, island_num, sinks, sink_num, threshold, dir_arr, code)

    # 如果没有主岛，则按type=5处理
    else:
        m_islands = []
        i_sinks = sinks
        basin, sub_num, b_types, b_areas, b_outlets, b_envelopes, other_outlets, outlet_merge_flag, other_sinks, \
            sink_merge_flag, m_island_merge_flag, island_merge_flag, i_sink_merge_flag = \
            divide_5(islands, island_num, sinks, sink_num, threshold, dir_arr, code)

    # 裁剪流域
    result = break_into_sub_basins(basin, dir_arr, upa_arr, elv_arr, sub_num, b_types, b_areas, b_outlets, b_envelopes,
                          outlet_merge_flag, other_outlets, sink_merge_flag, sinks, i_sink_merge_flag, i_sinks,
                          island_merge_flag, islands, m_island_merge_flag, m_islands, ul_offset, geotransform,
                          proj, threshold, code, folder, stat_db_path, sql_statement)

    return result


def divide_5(islands, island_num, sinks, sink_num, min_threshold, dir_arr, code):

    # 行列数
    rows, cols = dir_arr.shape
    # 建立流域类型数组
    btype_list = np.zeros((11,), dtype=np.uint8)
    # 建立流域面积数组
    barea_list = np.zeros((11,), dtype=np.float64)
    # 流域envelope矩阵
    envelopes = np.zeros((11, 4), dtype=np.int32)
    envelopes[:, 0] = rows
    envelopes[:, 1] = cols
    # 编码数
    code_idx = 1
    # 编码的岛屿数量
    di_island_num = 0
    # 已编码的岛屿流域
    coded_island_ids = []
    # 岛屿合并
    island_merge_flag = np.zeros((island_num, ), dtype=np.uint8)
    # 内流区合并
    sink_merge_flag = np.zeros((island_num, ), dtype=np.uint8)

    # 编码岛屿面积阈值
    island_threshold = min_threshold

    # 先从面积大的岛屿开始编码，需要有一个大岛屿的阈值
    while code_idx < 11 and di_island_num < island_num:
        if islands[di_island_num][6] > island_threshold:
            btype_list[code_idx] = 5
            envelopes[code_idx] = islands[di_island_num][8:12]
            island_merge_flag[di_island_num] = code_idx
            coded_island_ids.append(di_island_num)
            di_island_num += 1
            code_idx += 1
        else:
            break

    # 如果岛屿的面积都很小，则取面积最大的岛屿作为编码岛屿
    if di_island_num == 0:
        btype_list[code_idx] = 5
        envelopes[code_idx] = islands[di_island_num][8:12]
        island_merge_flag[di_island_num] = code_idx
        coded_island_ids.append(di_island_num)
        di_island_num += 1
        code_idx += 1

    # 计算每个岛屿对已编码岛屿外包矩形的改变
    frac = 0.02
    ref_cell_area = islands[0][7]
    size_change_threshold = max(min_threshold / ref_cell_area, rows * cols * frac)
    
    change_env = np.zeros((island_num, 11), dtype=np.int64)
    for i in range(island_num):
        for j in range(1, code_idx):
            change_env[i, j] = calc_enve_change(envelopes[j], islands[i][8:12])

    # 然后从其他岛屿中挑选改变外包矩形最大的岛屿作为补充编码
    while code_idx < 11 and di_island_num < island_num:
        # 计算对流域范围改变最大的岛屿集合
        min_changes = np.min(change_env[:, 1:code_idx], axis=1)
        max_change_island = np.argmax(min_changes)
        max_change_size = min_changes[max_change_island]
        # 如果岛屿集合改变流域外包矩形尺寸过大，则将这个岛屿集合单独编码
        if max_change_size > size_change_threshold:
            btype_list[code_idx] = 5
            temp_envelope = islands[max_change_island][8:12]
            envelopes[code_idx] = temp_envelope
            # 并更新差异矩阵
            for i in range(island_num):
                change_env[i, code_idx] = calc_enve_change(temp_envelope, islands[i][8:12])
            coded_island_ids.append(max_change_island)
            island_merge_flag[max_change_island] = code_idx
            code_idx += 1
            di_island_num += 1
        else:
            break

    # 进行岛屿合并
    island_merge_5(islands, island_num, island_merge_flag, coded_island_ids, rows, cols)

    # 对岛屿进行四连通域分析
    all_island_arr = np.zeros((rows, cols), dtype=np.uint8)
    all_island_arr[dir_arr != 247] = 1
    island_label_res, island_label_num = label(all_island_arr)
    # 四连通分类结果与数据库存储结果不一致，抛出错误
    if island_label_num != island_num:
        raise RuntimeError("The number of islands does not match in basin %s" % code)

    island_paint_flag = np.zeros((island_num + 1, ), dtype=np.uint32)
    for i in range(island_num):
        island_paint_flag[island_label_res[islands[i][3:5]]] = island_merge_flag[i]

    # 生成流域划分结果
    update_island_label(island_label_res, island_paint_flag, island_label_num)
    basin = island_label_res.astype(np.uint8)

    # 更新流域外包矩形
    for i in range(island_num):
        island_code = island_merge_flag[i]
        update_envelope(envelopes[island_code], islands[i][8:12])

    # 更新内流区合并结果
    for i in range(sink_num):
        sink_merge_flag[i] = basin[sinks[i][3:5]]

    return basin, code_idx - 1, btype_list, barea_list, [], envelopes, [], [], [], [], [], island_merge_flag, sink_merge_flag


def island_merge_5(islands, island_num, island_merge_flag, coded_islands, rows, cols):
    """

    :param islands:
    :param island_num:
    :param island_merge_flag:
    :param coded_islands:
    :param rows:
    :param cols:
    :return:
    """

    max_dst = float(rows + cols)
    min_dst_island = coded_islands[0]

    for i in range(island_num):
        if island_merge_flag[i] == 0:
            min_dst = max_dst
            for j in coded_islands:
                h_diff = islands[i][1] - islands[j][1]
                w_diff = islands[i][2] - islands[j][2]
                temp_dst = math.sqrt(h_diff * h_diff + w_diff * w_diff) - islands[i][5] - islands[j][5]
                if temp_dst < min_dst:
                    min_dst = temp_dst
                    min_dst_island = j
                island_merge_flag[i] = island_merge_flag[min_dst_island]

    return 1


def prepare_4(dir_arr, upa_arr, islands, island_num, sinks, sink_num, threshold):

    # 找到主岛
    all_edge = np.zeros(dir_arr.shape, dtype=np.uint8)
    all_edge[dir_arr == 0] = 1
    label_res, label_num = label(all_edge)
    main_island_label = label_res[islands[0][3:5]]
    main_island_mask = label_res == main_island_label
    temp_upa = upa_arr.copy()
    temp_upa[~main_island_mask] = -9999
    # 计算主要出水口
    outlet_idxs = np.argwhere(temp_upa > threshold)
    outlet_num = outlet_idxs.shape[0]
    # 对流域出水口面积进行排序
    outlet_area = np.zeros((outlet_num), dtype=np.float32)
    for i in range(outlet_num):
        outlet_area[i] = upa_arr[outlet_idxs[i, 0], outlet_idxs[i, 1]]    
    outlet_sort = np.argsort(-outlet_area)
    # 生成主要出水口列表
    outlets = [(int(outlet_idxs[idx, 0]), int(outlet_idxs[idx, 1]), float(outlet_area[idx])) for idx in outlet_sort]

    
    sp_idx = index.Index(interleaved=False)
    # 提取大陆边界上的主要外流区
    idx_list = np.argwhere(main_island_mask == True)
    mo_id = 1
    for loc_i, loc_j in idx_list:
        # 插入到R树中
        cor = (loc_j + 0.5, loc_j + 0.5, loc_i + 0.5, loc_i + 0.5)
        sp_idx.insert(mo_id, cor, obj=(loc_j, loc_i))
        mo_id += 1
    
    # 重新提取岛屿
    other_islands = []
    for i in range(1, island_num):
        temp = list(islands[i])
        # 更新岛屿到大陆之间的距离
        gc_cor = (temp[2], temp[2], temp[1], temp[1])
        nearest_j, nearest_i = list(sp_idx.nearest(gc_cor, objects="raw"))[0]
        nearest_dst = distance_2d((temp[2], temp[1]), (nearest_j, nearest_i)) - temp[5]
        is_type = 1 if nearest_dst < 10 and temp[6] < 0.1 else 2
        temp[12] = float(nearest_dst)
        temp[13] = int(nearest_i)
        temp[14] = int(nearest_j)
        temp[15] = is_type
        other_islands.append(tuple(temp))
    
    
    # 内流区列表
    m_sinks = []
    i_sinks = []
    for i in range(sink_num):
        sample_code = label_res[sinks[i][6:8]]
        if sample_code == main_island_label:
            temp = list(sinks[i])
            temp[8] = 1
            m_sinks.append(tuple(temp))
        else:
            i_sinks.append(sinks[i])

    return outlets, outlet_num, m_sinks, len(m_sinks), other_islands, len(other_islands), [], 0, i_sinks, len(i_sinks)


@jit(nopython=True)
def distance_2d(cor_a, cor_b):

    a2 = math.pow(cor_a[0] - cor_b[0], 2)
    b2 = math.pow(cor_a[1] - cor_b[1], 2)
    return math.sqrt(a2 + b2)


def break_into_sub_basins(basin_arr, dir_arr, upa_arr, elv_arr, sub_num, sub_types, sub_areas, sub_outlets, sub_enves,
                          outlet_merge_flag, outlets, sink_merge_flag, sinks, i_sink_merge_flag, i_sinks,
                          island_merge_flag, islands, m_island_merge_flag, m_islands,
                          ul_offset, bench_trans, proj, min_threshold, pre_code, path, stat_db_path, stat_sqline):
    """

    :param basin_arr:
    :param dir_arr:
    :param upa_arr:
    :param elv_arr:
    :param sub_num:
    :param sub_types:
    :param sub_areas:
    :param sub_outlets:
    :param sub_enves:
    :param outlet_merge_flag:
    :param outlets:
    :param sink_merge_flag:
    :param sinks:
    :param i_sink_merge_flag:
    :param i_sinks:
    :param island_merge_flag:
    :param islands:
    :param m_island_merge_flag:
    :param m_islands:
    :param ul_offset:
    :param bench_trans:
    :param proj:
    :param min_threshold:
    :param pre_code:
    :param path:
    :param stat_db_path:
    :param stat_sqline:
    :return:
    """

    ins_val_list = []


    #########################################
    #           如果没有划分出子流域            #
    #########################################
    if sub_num <= 1:
        cur_code = pre_code + '0'
        folder = os.path.join(path, '0')
        # 判断文件是否已经存在
        if not os.path.exists(folder):
            os.mkdir(folder)  # 创建子流域目录
        # 复制流域文件
        clone_basin(path, pre_code, folder, cur_code)

        # 创建与汇总数据库的连接
        ins_val = (cur_code, int(sub_types[1]), float(sub_areas[1]), -1, -1, -1, 0)
        ins_val_list.append(ins_val)
        
        return ins_val_list

    #########################################
    #             如果划分了子流域             #
    #########################################


    # 准备下一层级流域划分需要的输入
    for i in range(1, sub_num + 1):

        """ 路径检查 """
        # 如果编码结果为10，则用0代替
        if i == 10:
            cur_code = pre_code + str(0)
            folder = os.path.join(path, '0')
        else:
            cur_code = pre_code + str(i)
            folder = os.path.join(path, str(i))
        # 判断次级目录是否已经存在
        if not os.path.exists(folder):
            os.mkdir(folder)  # 创建子流域目录
        os.chdir(folder)  # 切换工作目录

        """ 裁剪至子流域 """
        # 地理参考
        min_row = int(sub_enves[i, 0] - 1)
        max_row = int(sub_enves[i, 2] + 2)
        min_col = int(sub_enves[i, 1] - 1)
        max_col = int(sub_enves[i, 3] + 2)
        sub_rows = max_row - min_row
        sub_cols = max_col - min_col
        ul_lat = bench_trans[3] + min_row * bench_trans[5]  # 左上角纬度
        ul_lon = bench_trans[0] + min_col * bench_trans[1]  # 左上角经度
        sub_geo_transform = (ul_lon, bench_trans[1], 0, ul_lat, 0, bench_trans[5])

        # 栅格数据
        mask = basin_arr[min_row:max_row, min_col:max_col] != i
        sub_dir_arr = dir_arr[min_row:max_row, min_col:max_col].copy()
        sub_dir_arr[mask] = 247
        array2tif(r'%s_dir.tif' % cur_code, sub_dir_arr, sub_geo_transform, proj, nd_value=247, dtype=1)
        sub_upa_arr = upa_arr[min_row:max_row, min_col:max_col].copy()
        sub_upa_arr[mask] = -9999
        array2tif(r'%s_upa.tif' % cur_code, sub_upa_arr, sub_geo_transform, proj, nd_value=247, dtype=6)
        sub_elv_arr = elv_arr[min_row:max_row, min_col:max_col].copy()
        sub_elv_arr[mask] = -9999
        array2tif(r'%s_elv.tif' % cur_code, sub_elv_arr, sub_geo_transform, proj, nd_value=247, dtype=6)

        # 矢量数据
        bas_arr = np.ones((sub_rows, sub_cols), dtype=np.uint8)
        bas_arr[mask] = 0
        shp_path = "%s.shp" % cur_code
        raster2shp_mem(shp_path, bas_arr, sub_geo_transform, proj, nd_value=0, dtype=1)

        """
            一共有5张表格:
            basin_property: 1,2,3,4,5
            outlets: 4
            sinks: 1,2,3,4,5    
            islands: 4,5
            geo_transform: 1,2,3,4,5
            
            geo_transform 所有流域类型都要计算，所以第一个算
            basin_property 要统计流域，所以最后一个算
            先判断1,2,3 采用相同的处理方法
            然后4
            最后5
        """

        # 创建数据库连接
        full_db_path = os.path.join(folder, "%s.db" % cur_code)
        conn = sqlite3.connect(full_db_path)
        cursor = conn.cursor()

        """ 地理参考表格"""
        create_gt_table(conn)
        ins_val = (ul_lon, bench_trans[1], 0, ul_lat, 0, bench_trans[5], sub_rows, sub_cols,
                   ul_offset[0] + min_row, ul_offset[1] + min_col)
        cursor.execute(gt_sql, ins_val)
        conn.commit()

        """ 流域属性表 """
        create_bp_table(conn)
        bas_type = int(sub_types[i])
        bas_area = float(sub_areas[i])
        total_area = bas_area
        outlet_lon = None
        outlet_lat = None
        outlet_loc_ridx = None
        outlet_loc_cidx = None
        total_sink_num = 0
        total_island_num = 0
        divisibility = 1

        ##########################
        #     1,2,3 (不含岛屿)    #
        ##########################
        if bas_type in [1, 2, 3]:

            # 处理流域出水口信息
            outlet_loc_ridx = int(sub_outlets[i][0] - min_row)
            outlet_loc_cidx = int(sub_outlets[i][1] - min_col)
            outlet_lat = bench_trans[3] + (sub_outlets[i][0] + 0.5) * bench_trans[5]
            outlet_lon = bench_trans[0] + (sub_outlets[i][1] + 0.5) * bench_trans[1]

            # 处理内流区信息
            merge_sink_ids = np.argwhere(sink_merge_flag == i)
            merge_sink_num = merge_sink_ids.shape[0]
            total_sink_num = merge_sink_num
            if total_sink_num > 0:
                create_sb_table(conn)  # 创建内流区表格
                for sink_id in merge_sink_ids:
                    temp = list(sinks[sink_id[0]])
                    total_area += temp[5]  # 总面积加上合并的内流区的面积
                    temp[1] -= min_row  # 更改内流区最低点在矩阵中的行号
                    temp[2] -= min_col  # 更改内流区最低点在矩阵中的列号
                    ins_val = tuple(temp)  # 重新打包成元组
                    cursor.execute(sb_sql, ins_val)
                conn.commit()

            divide_area = total_area
            # 判断是否可以继续划分子流域
            if bas_area < min_threshold and merge_sink_num < 1:
                divisibility = 0


        ##########################
        #      4 含岛屿和内流区     #
        ##########################
        elif bas_type == 4:

            # 处理外流区信息
            outlet_ids = np.argwhere(outlet_merge_flag == i)
            sub_outlet_num = outlet_ids.shape[0]
            if sub_outlet_num > 0:
                create_mo_table(conn)
                for outlet_id in outlet_ids:
                    temp = list(outlets[outlet_id[0]])
                    temp[0] -= min_row
                    temp[1] -= min_col
                    ins_val = tuple(temp)
                    cursor.execute(mo_sql, ins_val)
                conn.commit()

            # 处理内流区信息
            merge_sink_ids = np.argwhere(sink_merge_flag == i)
            merge_sink_num = merge_sink_ids.shape[0]
            merge_i_sink_ids = np.argwhere(i_sink_merge_flag == i)
            merge_i_sink_num = merge_i_sink_ids.shape[0]
            total_sink_num = merge_sink_num + merge_i_sink_num
            if total_sink_num > 0:
                create_sb_table(conn)

            # 处理大陆内流区信息
            if merge_sink_num > 0:
                for sink_id in merge_sink_ids:
                    temp = list(sinks[sink_id[0]])
                    total_area += temp[5]  # 总面积加上合并的内流区的面积
                    temp[1] -= min_row  # 更改内流区最低点在矩阵中的行号
                    temp[2] -= min_col  # 更改内流区最低点在矩阵中的列号
                    ins_val = tuple(temp)  # 重新打包成元组
                    cursor.execute(sb_sql, ins_val)
                conn.commit()

            # 处理岛屿内流区信息
            if merge_i_sink_num > 0:
                for sink_id in merge_i_sink_ids:
                    temp = list(i_sinks[sink_id[0]])
                    temp[1] -= min_row  # 更改内流区最低点在矩阵中的行号
                    temp[2] -= min_col  # 更改内流区最低点在矩阵中的列号
                    temp[6] -= min_row  # 更改岛屿内流区对应岛屿样点的索引
                    temp[7] -= min_col
                    ins_val = tuple(temp)
                    cursor.execute(is_sql, ins_val)
                conn.commit()

            # 处理岛屿信息
            merge_island_ids = np.argwhere(island_merge_flag == i)
            merge_island_num = merge_island_ids.shape[0]
            merge_m_island_ids = np.argwhere(m_island_merge_flag == i)
            merge_m_island_num = merge_m_island_ids.shape[0]
            total_island_num = merge_island_num + merge_m_island_num
            if total_island_num > 0:
                create_is_table(conn)

            # 处理远海岛屿信息
            if merge_island_num > 0:
                for island_id in merge_island_ids:
                    temp = list(islands[island_id[0]])
                    total_area += temp[6]
                    temp[1] -= min_row
                    temp[2] -= min_col
                    temp[3] -= min_row
                    temp[4] -= min_col
                    temp[8] -= min_row
                    temp[9] -= min_col
                    temp[10] -= min_row
                    temp[11] -= min_col
                    temp[13] -= min_row
                    temp[14] -= min_col
                    ins_val = tuple(temp)
                    cursor.execute(is_sql, ins_val)
                conn.commit()

            # 处理大陆附属岛屿信息
            if merge_m_island_num > 0:
                for island_id in merge_m_island_ids:
                    temp = list(m_islands[island_id[0]])
                    total_area += temp[6]
                    temp[1] -= min_row
                    temp[2] -= min_col
                    temp[3] -= min_row
                    temp[4] -= min_col
                    temp[8] -= min_row
                    temp[9] -= min_col
                    temp[10] -= min_row
                    temp[11] -= min_col
                    temp[13] -= min_row
                    temp[14] -= min_col
                    ins_val = tuple(temp)
                    cursor.execute(is_sql, ins_val)
                conn.commit()

            divide_area = total_area
            # 判断是否可以继续划分子流域
            if sub_outlet_num < 1 :
                divisibility = 0
            

        ###############################
        #        5 岛屿和岛屿内流区      #
        ###############################
        elif bas_type == 5:

            # 处理岛屿信息
            merge_island_ids = np.argwhere(island_merge_flag == i)
            merge_island_num = merge_island_ids.shape[0]
            total_island_num = merge_island_num
            if merge_island_num <= 0:
                raise RuntimeError("No island in basin %s, type 5!" % cur_code)

            ref_cell_area = islands[merge_island_ids[0][0]][7]
            create_is_table(conn)
            for island_id in merge_island_ids:
                temp = list(islands[island_id[0]])
                total_area += temp[6]
                temp[1] -= min_row
                temp[2] -= min_col
                temp[3] -= min_row
                temp[4] -= min_col
                temp[8] -= min_row
                temp[9] -= min_col
                temp[10] -= min_row
                temp[11] -= min_col
                temp[13] -= min_row
                temp[14] -= min_col
                ins_val = tuple(temp)
                cursor.execute(is_sql, ins_val)
            conn.commit()

            # 处理岛屿内流区信息
            merge_i_sink_ids = np.argwhere(i_sink_merge_flag == i)
            merge_i_sink_num = merge_i_sink_ids.shape[0]
            total_sink_num = merge_i_sink_num
            if total_sink_num > 0:
                create_sb_table(conn)
                for sink_id in merge_i_sink_ids:
                    temp = list(i_sinks[sink_id[0]])
                    temp[1] -= min_row  # 更改内流区最低点在矩阵中的行号
                    temp[2] -= min_col  # 更改内流区最低点在矩阵中的列号
                    temp[6] -= min_row  # 更改岛屿内流区对应岛屿样点的索引
                    temp[7] -= min_col
                    ins_val = tuple(temp)
                    cursor.execute(is_sql, ins_val)
                conn.commit()

            divide_area = (sub_rows - 2) * (sub_cols - 2) * ref_cell_area
            if divide_area < min_threshold:
                divisibility = 0
            if total_island_num == 1 and total_area < min_threshold:
                divisibility = 0

        else:
            print(sub_types)
            print(sub_num)
            raise RuntimeError("type of basin %s in path: %s was not in expectation 1-to-5." % (cur_code, path))

        # 向数据库中插入流域属性数据
        ins_val = (bas_type, bas_area, total_area, outlet_lon, outlet_lat,
                   outlet_loc_ridx, outlet_loc_cidx, total_sink_num, total_island_num)
        cursor.execute(bp_sql, ins_val)
        conn.commit()
        conn.close()

        ins_val = (cur_code, bas_type, total_area, divide_area, total_sink_num, total_island_num, divisibility)
        ins_val_list.append(ins_val)
        
    return ins_val_list
    