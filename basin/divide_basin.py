import math
import os
import sys
sys.path.append(r"../")
import numpy as np
import db_op as dp
import preprocess as prep
from util import raster
from util import interface as cfunc
from numba import jit


@jit(nopython=True)
def ravel_to_1dim(idx, cols):
    return idx[0] * cols + idx[1]


def divide_basin_1(src_info, root, threshold):

    # 解析工作路径
    str_src_code = str(src_info[0])
    src_folder = os.path.join(root, *str_src_code)
    src_tif = os.path.join(src_folder, str_src_code + ".tif")
    src_db = os.path.join(src_folder, str_src_code + '.db')

    # 查询流域成员信息
    basin_type, area, total_area, outlet_idx, inlet_idx, mOutletNum, mRegionNum, iRegionNum, cluster_num,\
        mOutlets, mRegions, iRegions, sinks, clusters, islands, samples, clusterDst \
        = dp.get_basin_components(src_db)
    # 从数据库中查询子流域的位置信息
    ul_offset = dp.get_ul_offset(src_db)
    # 读取当前流域的流向，汇流累积量和高程数据
    dir_arr, upa_arr, elv_arr, geo_trans, proj = \
        raster.read_tif_files(root, mRegionNum + iRegionNum, src_tif, ul_offset)

    # 流域划分
    basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
        sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands = \
        divide_1(outlet_idx, inlet_idx, dir_arr, upa_arr, elv_arr, threshold, mRegions, mRegionNum, sinks)

    # 分割流域，并保存为新的输入
    result = break_into_sub_basins(basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas,
                                   sub_envelopes, sub_samples, sub_outlets, sub_inlets, sub_mOutlets,
                                   sub_mRegions, sub_iRegions, sub_clusters, sub_islands, clusterDst,
                                   mOutlets, mRegions, iRegions, sinks, clusters, islands,
                                   ul_offset, geo_trans, proj, threshold, root, src_info)

    return result


def divide_1(outlet_idx, inlet_idx, dir_arr, upa_arr, elv_arr, threshold, mRegions, mRegionNum, sinks):
    # 初始化流域划分基本信息
    sub_types = np.zeros((11,), dtype=np.uint8)  # 子流域类型
    sub_outlets = np.zeros((11, 2), dtype=np.int32)  # 子流域出水口
    sub_inlets = np.zeros((11, 2), dtype=np.int32)  # 子流域入水口
    sub_areas = np.zeros((11,), dtype=np.float64)  # 子流域面积
    sub_total_areas = np.zeros((11,), dtype=np.float64)  # 子流域总面积
    sub_downs = np.zeros((11, ), dtype=np.uint8)
    sub_envelopes = np.zeros((11, 4), dtype=np.int32)  # 子流域外包矩形
    sub_samples = np.zeros((11, 4), dtype=np.int32)  # 子流域大陆海岸线样点
    basin = np.zeros(dir_arr.shape, dtype=np.uint8)  # 子流域划分结果
    rows, cols = dir_arr.shape
    sub_envelopes[1:, 0] = rows
    sub_envelopes[1:, 1] = cols
    sub_mOutlets = {i: [] for i in range(1, 11)}
    sub_mRegions = {i: [] for i in range(1, 11)}
    sub_iRegions = {i: [] for i in range(1, 11)}
    sub_clusters = {i: [] for i in range(1, 11)}
    sub_islands = {i: [] for i in range(1, 11)}

    # 计算逆d8流向
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    # pfafstetter编码划分子流域
    sub_num = cfunc.pfafstetter(outlet_idx, inlet_idx, threshold, re_dir_arr, upa_arr, basin, sub_outlets, sub_inlets)
    if sub_num % 2 == 0:
        raise RuntimeError("the number of sub basins is even in case of pfafstetter 1!")
    head_water_code = sub_num

    # 计算每个子流域的流域类型和流域面积
    sub_types[sub_num] = 1
    sub_areas[sub_num] = upa_arr[tuple(sub_outlets[sub_num])]
    sub_total_areas[sub_num] = sub_areas[sub_num]
    upstream_area = sub_areas[sub_num]
    for i in range(sub_num - 1, 1, -2):
        # 偶数编码流域
        sub_types[i] = 1
        sub_areas[i] = upa_arr[tuple(sub_outlets[i])]
        sub_total_areas[i] = sub_areas[i]
        upstream_area += sub_areas[i]
        # 奇数编码流域
        sub_types[i - 1] = 2
        sub_areas[i - 1] = upa_arr[tuple(sub_outlets[i - 1])] - upstream_area
        sub_total_areas[i - 1] = sub_areas[i - 1]
        upstream_area += sub_areas[i - 1]
    # 计算下游子流域的编号
    for i in range(2, sub_num, 2):
        sub_downs[i] = i - 1
        sub_downs[i + 1] = i - 1

    # 一个层级可以编码1~10共10个子流域，而流域划分最多编码到9，剩下的编码位置可以用内流区补足
    diRegionNum = min(mRegionNum, 10 - sub_num)
    # 处理未直接编码的内流区
    for i in range(diRegionNum, mRegionNum):
        di_sinkIDs = mRegions[i].sinks
        sink_idxs = np.empty(di_sinkIDs.shape, dtype=np.uint64)
        for probe, sink_id in enumerate(di_sinkIDs):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)

        attached_basin = cfunc.get_region_attached_basin(sink_idxs, re_dir_arr, elv_arr, basin)
        sub_total_areas[attached_basin] += mRegions[i].area
        sub_mRegions[attached_basin].append(i)

        sink_colors = np.full(sink_idxs.shape, fill_value=attached_basin, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)

    # 处理直接编码的内流区
    for i in range(diRegionNum):
        sub_num += 1
        sub_types[sub_num] = 3
        sub_areas[sub_num] = mRegions[i].area
        sub_total_areas[sub_num] = sub_areas[sub_num]
        sub_mRegions[sub_num].append(i)

        di_sinkIDs = mRegions[i].sinks
        sink_idxs = np.empty(di_sinkIDs.shape, dtype=np.uint64)
        for probe, sink_id in enumerate(di_sinkIDs):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)
        sink_colors = np.full(sink_idxs.shape, fill_value=sub_num, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)

    # 计算子流域外包矩形
    cfunc.get_basin_envelopes(basin, sub_envelopes)

    return basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
        sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands


def divide_basin_2(src_info, root, threshold):

    # 解析工作路径
    str_src_code = str(src_info[0])
    src_folder = os.path.join(root, *str_src_code)
    src_tif = os.path.join(src_folder, str_src_code + ".tif")
    src_db = os.path.join(src_folder, str_src_code + '.db')

    # 查询流域成员信息
    basin_type, area, total_area, outlet_idx, inlet_idx, mOutletNum, mRegionNum, iRegionNum, cluster_num,\
        mOutlets, mRegions, iRegions, sinks, clusters, islands, samples, clusterDst \
        = dp.get_basin_components(src_db)
    # 从数据库中查询子流域的位置信息
    ul_offset = dp.get_ul_offset(src_db)
    # 读取当前流域的流向，汇流累积量和高程数据
    dir_arr, upa_arr, elv_arr, geo_trans, proj = \
        raster.read_tif_files(root, mRegionNum + iRegionNum, src_tif, ul_offset)
    # 流域划分
    basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
        sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands = \
        divide_2(outlet_idx, inlet_idx, area, dir_arr, upa_arr, elv_arr, threshold, mRegions, mRegionNum, sinks)

    # 分割流域，并保存为新的输入
    result = break_into_sub_basins(basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas,
                                   sub_envelopes, sub_samples, sub_outlets, sub_inlets, sub_mOutlets,
                                   sub_mRegions, sub_iRegions, sub_clusters, sub_islands, clusterDst,
                                   mOutlets, mRegions, iRegions, sinks, clusters, islands,
                                   ul_offset, geo_trans, proj, threshold, root, src_info)

    return result


def divide_2(outlet_idx, inlet_idx, area, dir_arr, upa_arr, elv_arr, threshold, mRegions, mRegionNum, sinks):
    # 初始化流域划分基本信息
    sub_types = np.zeros((11,), dtype=np.uint8)  # 子流域类型
    sub_outlets = np.zeros((11, 2), dtype=np.int32)  # 子流域出水口
    sub_inlets = np.zeros((11, 2), dtype=np.int32)  # 子流域入水口
    sub_areas = np.zeros((11,), dtype=np.float64)  # 子流域面积
    sub_total_areas = np.zeros((11,), dtype=np.float64)  # 子流域总面积
    sub_downs = np.zeros((11,), dtype=np.uint8)
    sub_envelopes = np.zeros((11, 4), dtype=np.int32)  # 子流域外包矩形
    sub_samples = np.zeros((11, 4), dtype=np.int32)  # 子流域大陆海岸线样点
    basin = np.zeros(dir_arr.shape, dtype=np.uint8)  # 子流域划分结果
    rows, cols = dir_arr.shape
    sub_envelopes[1:, 0] = rows
    sub_envelopes[1:, 1] = cols
    sub_mOutlets = {i: [] for i in range(1, 11)}
    sub_mRegions = {i: [] for i in range(1, 11)}
    sub_iRegions = {i: [] for i in range(1, 11)}
    sub_clusters = {i: [] for i in range(1, 11)}
    sub_islands = {i: [] for i in range(1, 11)}

    # 计算逆d8流向
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    # pfafstetter编码划分子流域
    sub_num = cfunc.pfafstetter(outlet_idx, inlet_idx, threshold, re_dir_arr, upa_arr, basin, sub_outlets, sub_inlets)

    # 计算每个子流域的流域类型和流域面积
    # 如果未划分出子流域，且当前流域较大，尝试对加密划分
    if sub_num == 1 and area >= 2.5 * threshold:
        di_sub_num = min(math.floor(area / threshold), 9)
        basin[:, :] = 0
        cfunc.decompose(outlet_idx, inlet_idx, area, di_sub_num, dir_arr, re_dir_arr, upa_arr,
                        basin, sub_outlets, sub_inlets)
        sub_types[1:di_sub_num + 1] = 2
        upstream_area = upa_arr[outlet_idx] - area
        for i in range(di_sub_num, 0, -1):
            sub_areas[i] = upa_arr[tuple(sub_outlets[i])] - upstream_area
            sub_total_areas[i] = sub_areas[i]
            upstream_area += sub_areas[i]
        for i in range(1, di_sub_num):
            sub_downs[i + 1] = i
        # 最上游的流域承接上游来水
        head_water_code = di_sub_num
        sub_num = di_sub_num

    # 如果划分出了多个子流域
    else:
        di_sub_num = sub_num
        upstream_area = upa_arr[outlet_idx] - area
        # 如果划分出了奇数个子流域，先处理最上游的子流域
        if sub_num % 2 == 1:
            sub_types[sub_num] = 2
            sub_areas[sub_num] = upa_arr[tuple(sub_outlets[sub_num])] - upstream_area
            sub_total_areas[sub_num] = sub_areas[sub_num]
            upstream_area += sub_areas[sub_num]
            di_sub_num -= 1
            # 最上游的奇数编号流域承接上游来水
            head_water_code = sub_num
            # 最上游流域的下游流域，注意sub_num=1的特殊情况
            sub_downs[sub_num] = sub_num - 2 if sub_num > 2 else 0
        else:
            # 确保承接上游来水的为奇数号流域
            head_water_code = sub_num - 1

        # 之后处理下游的子流域
        for i in range(di_sub_num, 1, -2):
            # 偶数编码流域
            sub_types[i] = 1
            sub_areas[i] = upa_arr[tuple(sub_outlets[i])]
            sub_total_areas[i] = sub_areas[i]
            upstream_area += sub_areas[i]
            # 奇数编码流域
            sub_types[i - 1] = 2
            sub_areas[i - 1] = upa_arr[tuple(sub_outlets[i - 1])] - upstream_area
            sub_total_areas[i - 1] = sub_areas[i - 1]
            upstream_area += sub_areas[i - 1]
        # 计算下游
        for i in range(2, di_sub_num, 2):
            sub_downs[i] = i - 1
            sub_downs[i + 1] = i - 1
        sub_downs[di_sub_num] = di_sub_num - 1 if di_sub_num > 0 else 0

    # 一个层级可以编码1~10共10个子流域，而流域划分最多编码到9，剩下的编码位置可以用内流区补足
    diRegionNum = min(mRegionNum, 10 - sub_num)
    # 处理未直接编码的内流区
    # 处理未直接编码的内流区
    for i in range(diRegionNum, mRegionNum):
        di_sinkIDs = mRegions[i].sinks
        sink_idxs = np.empty(di_sinkIDs.shape, dtype=np.uint64)
        for probe, sink_id in enumerate(di_sinkIDs):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)

        attached_basin = cfunc.get_region_attached_basin(sink_idxs, re_dir_arr, elv_arr, basin)
        sub_total_areas[attached_basin] += mRegions[i].area
        sub_mRegions[attached_basin].append(i)

        sink_colors = np.full(sink_idxs.shape, fill_value=attached_basin, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)

    # 处理直接编码的内流区
    for i in range(diRegionNum):
        sub_num += 1
        sub_types[sub_num] = 3
        sub_areas[sub_num] = mRegions[i].area
        sub_total_areas[sub_num] = sub_areas[sub_num]
        sub_mRegions[sub_num].append(i)

        di_sinkIDs = mRegions[i].sinks
        sink_idxs = np.empty(di_sinkIDs.shape, dtype=np.uint64)
        for probe, sink_id in enumerate(di_sinkIDs):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)
        sink_colors = np.full(sink_idxs.shape, fill_value=sub_num, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)

    # 计算子流域外包矩形
    cfunc.get_basin_envelopes(basin, sub_envelopes)

    return basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
        sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands


def divide_basin_3(src_info, root, threshold):

    # 解析工作路径
    str_src_code = str(src_info[0])
    src_folder = os.path.join(root, *str_src_code)
    src_tif = os.path.join(src_folder, str_src_code + ".tif")
    src_db = os.path.join(src_folder, str_src_code + '.db')

    # 查询流域成员信息
    basin_type, area, total_area, outlet_idx, inlet_idx, mOutletNum, mRegionNum, iRegionNum, cluster_num,\
        mOutlets, mRegions, iRegions, sinks, clusters, islands, samples, clusterDst \
        = dp.get_basin_components(src_db)
    # 从数据库中查询子流域的位置信息
    ul_offset = dp.get_ul_offset(src_db)
    # 读取当前流域的流向，汇流累积量和高程数据
    dir_arr, upa_arr, elv_arr, geo_trans, proj = \
        raster.read_tif_files(root, mRegionNum + iRegionNum, src_tif, ul_offset)

    sinkIDs = mRegions[0].sinks.copy()
    sink_num = sinkIDs.shape[0]

    # 如果只有1个内流流域
    if sink_num == 1:
        outlet_idx = sinks[sinkIDs[0]].loc
        inlet_idx = (0, 0)
        mRegions = {}
        mRegionNum = 0
        sinks = {}

        basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
            sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands = \
            divide_1(outlet_idx, inlet_idx, dir_arr, upa_arr, elv_arr, threshold, mRegions, mRegionNum, sinks)

    # 如果有多个内流流域，但是最大的内流流域面积占比超过70%
    elif sinks[sinkIDs[0]].area > mRegions[0].area * 0.7:

        outlet_idx, inlet_idx, mRegions, mRegionNum = prepare_1_from_3(mRegions, sinks, dir_arr)
        sinks.pop(sinkIDs[0])

        basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
            sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands = \
            divide_1(outlet_idx, inlet_idx, dir_arr, upa_arr, elv_arr, threshold, mRegions, mRegionNum, sinks)

    else:
        basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
            sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands = \
            divide_3(dir_arr, elv_arr, mRegions, sinks, sink_num)

    # 分割流域，并保存为新的输入
    result = break_into_sub_basins(basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas,
                                   sub_envelopes, sub_samples, sub_outlets, sub_inlets, sub_mOutlets,
                                   sub_mRegions, sub_iRegions, sub_clusters, sub_islands, clusterDst,
                                   mOutlets, mRegions, iRegions, sinks, clusters, islands,
                                   ul_offset, geo_trans, proj, threshold, root, src_info)

    return result


def prepare_1_from_3(mRegions, sinks, dir_arr):

    rows, cols = dir_arr.shape
    sinkIDS = mRegions[0].sinks
    outlet_idx = sinks[sinkIDS[0]].loc
    inlet_idx = (0, 0)

    new_sinksIDS = sinkIDS[1:].copy()
    sink_num = new_sinksIDS.shape[0]
    sink_idxs = np.empty((sink_num, ), dtype=np.uint64)
    sink_areas = np.empty((sink_num, ), dtype=np.float32)
    for i in range(sink_num):
        sink_id = new_sinksIDS[i]
        sink_idxs[i] = ravel_to_1dim(sinks[sink_id].loc, cols)
        sink_areas[i] = sinks[sink_id].area

    region_flag, region_num = cfunc.sink_region(sink_idxs, sink_areas, dir_arr)
    region_areas = np.zeros((region_num + 1, ), dtype=np.float64)
    for i in range(0, sink_num):
        region_areas[region_flag[i + 1]] += sink_areas[i]

    new_mRegions = {}
    region_island = mRegions[0].location
    for i in range(1, region_num + 1):
        region_sinks = np.argwhere(region_flag == i).ravel()
        region_sinkIDs = sinkIDS[region_sinks]
        area = float(region_areas[i])
        region_sinks = region_sinkIDs.astype(np.int32)
        new_mRegions[i - 1] = dp.Region((area, region_island, region_sinks.tobytes()))

    return outlet_idx, inlet_idx, new_mRegions, region_num


def divide_3(dir_arr, elv_arr, mRegions, sinks, sink_num):
    # 初始化流域划分基本信息
    sub_types = np.zeros((11,), dtype=np.uint8)  # 子流域类型
    sub_outlets = np.zeros((11, 2), dtype=np.int32)  # 子流域出水口
    sub_inlets = np.zeros((11, 2), dtype=np.int32)  # 子流域入水口
    sub_areas = np.zeros((11,), dtype=np.float64)  # 子流域面积
    sub_total_areas = np.zeros((11,), dtype=np.float64)  # 子流域总面积
    sub_downs = np.zeros((11,), dtype=np.uint8)
    sub_envelopes = np.zeros((11, 4), dtype=np.int32)  # 子流域外包矩形
    sub_samples = np.zeros((11, 4), dtype=np.int32)  # 子流域大陆海岸线样点
    basin = np.zeros(dir_arr.shape, dtype=np.uint8)  # 子流域划分结果
    rows, cols = dir_arr.shape
    sub_envelopes[1:, 0] = rows
    sub_envelopes[1:, 1] = cols
    sub_mOutlets = {i: [] for i in range(1, 11)}
    sub_mRegions = {i: [] for i in range(1, 11)}
    sub_iRegions = {i: [] for i in range(1, 11)}
    sub_clusters = {i: [] for i in range(1, 11)}
    sub_islands = {i: [] for i in range(1, 11)}

    # 计算逆d8流向
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)

    sinkIDS = mRegions[0].sinks
    if sink_num <= 10:
        sub_num = sink_num
        sink_idxs = np.empty((sink_num,), dtype=np.uint64)
        for probe, sink_id in enumerate(sinkIDS):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)
        sink_colors = np.arange(start=1, stop=sink_num + 1, step=1, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)
    else:
        sink_idxs = np.empty((sink_num, ), dtype=np.uint64)
        sink_areas = np.empty((sink_num, ), dtype=np.float32)
        for i in range(sink_num):
            sink_id = sinkIDS[i]
            sink_idxs[i] = ravel_to_1dim(sinks[sink_id].loc, cols)
            sink_areas[i] = sinks[sink_id].area
        sub_num = cfunc.region_decompose_uint8(sink_idxs, sink_areas, re_dir_arr, elv_arr, basin)

    merge_flag = np.zeros((sink_num,), dtype=np.uint8)
    sink_area = np.zeros((sink_num,), dtype=np.float64)
    for i in range(sink_num):
        merge_flag[i] = basin[sinks[sinkIDS[i]].loc]
        sink_area[i] = sinks[sinkIDS[i]].area

    if np.count_nonzero(merge_flag) < sink_num:
        raise RuntimeError("There is some sink not processed!")

    location = mRegions[0].location
    for i in range(1, sub_num + 1):
        mask = merge_flag == i
        sub_types[i] = 3
        sub_areas[i] = np.sum(sink_area[mask])
        sub_total_areas[i] = sub_areas[i]
        record = (float(sub_areas[i]), location, sinkIDS[mask].tobytes())
        mRegions[i] = dp.Region(record)
        sub_mRegions[i].append(i)

    cfunc.get_basin_envelopes(basin, sub_envelopes)
    headwater_code = 1

    return basin, sub_num, headwater_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
        sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands


def divide_basin_4(src_info, root, threshold):

    # 解析工作路径
    str_src_code = str(src_info[0])
    src_folder = os.path.join(root, *str_src_code)
    src_tif = os.path.join(src_folder, str_src_code + ".tif")
    src_db = os.path.join(src_folder, str_src_code + '.db')

    # 查询流域成员信息
    basin_type, area, total_area, outlet_idx, inlet_idx, mOutletNum, mRegionNum, iRegionNum, cluster_num,\
        mOutlets, mRegions, iRegions, sinks, clusters, islands, samples, clusterDst \
        = dp.get_basin_components(src_db)
    # 从数据库中查询子流域的位置信息
    ul_offset = dp.get_ul_offset(src_db)
    # 读取当前流域的流向，汇流累积量和高程数据
    dir_arr, upa_arr, elv_arr, geo_trans, proj = \
        raster.read_tif_files(root, mRegionNum + iRegionNum, src_tif, ul_offset)

    basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
        sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands = \
        divide_4(samples, clusterDst, mOutlets, mRegions, iRegions, sinks, clusters, islands,
                 dir_arr, upa_arr, elv_arr, cluster_num, mOutletNum, mRegionNum, iRegionNum)

    # 分割流域，并保存为新的输入
    result = break_into_sub_basins(basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas,
                                   sub_envelopes, sub_samples, sub_outlets, sub_inlets, sub_mOutlets,
                                   sub_mRegions, sub_iRegions, sub_clusters, sub_islands, clusterDst,
                                   mOutlets, mRegions, iRegions, sinks, clusters, islands,
                                   ul_offset, geo_trans, proj, threshold, root, src_info)
    return result


def divide_4(samples, clusterDst, outlets, mRegions, iRegions, sinks, clusters, islands,
             dir_arr, upa_arr, elv_arr, cluster_num, outlet_num, mRegionNum, iRegionNum):
    # 初始化流域划分基本信息
    sub_types = np.zeros((11,), dtype=np.uint8)  # 子流域类型
    sub_inlets = np.zeros((11, 2), dtype=np.int32)  # 子流域入水口
    sub_outlets = np.zeros((11, 2), dtype=np.int32)  # 子流域出水口
    sub_areas = np.zeros((11,), dtype=np.float64)  # 子流域面积
    sub_total_areas = np.zeros((11,), dtype=np.float64)  # 子流域总面积
    sub_downs = np.zeros((11, ), dtype=np.uint8)
    sub_envelopes = np.zeros((11, 4), dtype=np.int32)  # 子流域外包矩形
    sub_samples = np.zeros((11, 2), dtype=np.int32)  # 子流域大陆海岸线样点
    rows, cols = dir_arr.shape
    sub_envelopes[1:, 0] = rows
    sub_envelopes[1:, 1] = cols
    sub_mOutlets = {i: [] for i in range(1, 11)}
    sub_mRegions = {i: [] for i in range(1, 11)}
    sub_iRegions = {i: [] for i in range(1, 11)}
    sub_clusters = {i: [] for i in range(1, 11)}
    sub_islands = {i: [] for i in range(1, 11)}
    sub_num = 0

    """
        first coding stage.
    """
    mainland_samples = np.frombuffer(samples, dtype=np.int32).reshape(-1, 2)
    pd_num = mainland_samples.shape[0]
    diOutletNum = diRegionNum = diClusterNum = 0
    diClusterIDs = []

    while pd_num < 9 and diOutletNum < outlet_num:
        di_outlet_area = outlets[diOutletNum].area
        di_region_area = 0.0 if diRegionNum >= mRegionNum else mRegions[diRegionNum].area
        di_cluster_area = 0.0 if diClusterNum >= cluster_num else clusters[diClusterNum].area

        if di_outlet_area >= di_region_area and di_outlet_area >= di_cluster_area:
            diOutletNum += 1
            pd_num += 2
        elif di_region_area >= di_outlet_area and di_region_area >= di_cluster_area:
            diRegionNum += 1
            pd_num += 1
        else:
            diClusterIDs.append(diClusterNum)
            diClusterNum += 1
            pd_num += 1

    """
        Second coding stage.
        When 
    """
    code_threshold = outlets[diOutletNum - 1].area / 3.0 if diOutletNum >= 1 else 0.0
    while pd_num < 10:
        di_region_area = 0.0 if diRegionNum >= mRegionNum else mRegions[diRegionNum].area
        di_cluster_area = 0.0 if diClusterNum >= cluster_num else clusters[diClusterNum].area
        if di_region_area == 0.0 and di_cluster_area == 0.0:
            break
        if di_region_area >= di_cluster_area and di_region_area >= code_threshold:
            diRegionNum += 1
            pd_num += 1
        elif di_cluster_area >= di_region_area and di_cluster_area >= code_threshold:
            diClusterIDs.append(diClusterNum)
            diClusterNum += 1
            pd_num += 1
        else:
            break

    """
        Third coding stage
        如果没有编码岛屿，而且编码未满。
        挑选离大陆最远的一个岛屿聚类，如果距离超过阈值，赋予该岛屿聚类编码。
    """
    if pd_num < 10 and diClusterNum == 0:
        # 找到距离大陆最远的岛屿聚类
        farthestCluster_id = -1
        farthest_distance = 0.0
        for i in range(0, cluster_num):
            if clusters[i].distance > farthest_distance:
                farthestCluster_id = i
                farthest_distance = clusters[i].distance
        if farthest_distance > math.sqrt(rows**2 + cols**2) / 2:
            diClusterNum += 1
            pd_num += 1
            diClusterIDs.append(farthestCluster_id)

    """
        Deal with endorheic basins.
    """
    mainland_edge = np.zeros(dir_arr.shape, dtype=np.uint8)
    mSample_num = mainland_samples.shape[0]
    mSampleIndexes = np.empty((mSample_num, ), dtype=np.uint64)
    probe = 0
    for ridx, cidx in mainland_samples:
        mSampleIndexes[probe] = ravel_to_1dim((int(ridx), int(cidx)), cols)
    mSampleColors = np.full((mSample_num, ), fill_value=1, dtype=np.uint8)
    cfunc.calc_coastal_edge(mSampleIndexes, mSampleColors, dir_arr, mainland_edge)

    # 在主要外流出水口出打断大陆海岸线
    for moID in range(diOutletNum):
        mainland_edge[outlets[moID].loc] = 0

    # inter-basins
    mainland_label_res, mainland_label_num = cfunc.label(mainland_edge)
    del mainland_edge
    basin = mainland_label_res.astype(np.uint8)
    del mainland_label_res

    # 统计inter-basins面积
    temp_basin_areas = cfunc.calc_coastal_basin_area(basin, mainland_label_num, upa_arr)
    for i in range(1, mainland_label_num + 1):
        sub_num += 1
        sub_types[sub_num] = 4
        sub_areas[sub_num] = temp_basin_areas[i]
        sub_total_areas[sub_num] = sub_areas[sub_num]

    # basins
    for i in range(diOutletNum):
        sub_num += 1
        outlet_idx = outlets[i].loc
        basin[outlet_idx] = sub_num
        sub_types[sub_num] = 1
        sub_outlets[sub_num] = outlet_idx
        sub_areas[sub_num] = upa_arr[outlet_idx]
        sub_total_areas[sub_num] = sub_areas[sub_num]

    # inter-basin mainland coastline samples
    for i in range(diOutletNum):
        ridx, cidx = outlets[i].loc
        nbrs = [(ridx, cidx + 1), (ridx + 1, cidx), (ridx, cidx - 1), (ridx - 1, cidx)]
        for idx in nbrs:
            if 1 <= basin[idx] <= mainland_label_num:
                sub_samples[basin[idx]] = idx
    for ridx, cidx in mainland_samples:
        if sub_samples[basin[ridx, cidx], 0] == 0:
            sub_samples[basin[ridx, cidx]] = (ridx, cidx)

    # 统计未编码河流的位于哪些流域
    for i in range(diOutletNum, outlet_num):
        sub_mOutlets[basin[outlets[i].loc]].append(i)

    # 追踪大陆外流区
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    cfunc.paint_up_mosaiced_uint8(re_dir_arr, basin)

    """
        Deal with exorheic basins.
    """
    # 处理未参与编码的内流区
    for region_id in range(diRegionNum, mRegionNum):
        sinkIDs = mRegions[region_id].sinks
        sink_idxs = np.empty(sinkIDs.shape, dtype=np.uint64)
        for probe, sink_id in enumerate(sinkIDs):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)

        attached_basin = cfunc.get_region_attached_basin(sink_idxs, re_dir_arr, elv_arr, basin)
        sub_total_areas[attached_basin] += mRegions[region_id].area
        sub_mRegions[attached_basin].append(region_id)

        sink_colors = np.full(sink_idxs.shape, fill_value=attached_basin, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)

    # 处理参与编码的内流区
    for region_id in range(diRegionNum):
        sub_num += 1
        sub_types[sub_num] = 3
        sub_areas[sub_num] = mRegions[region_id].area
        sub_total_areas[sub_num] = sub_areas[sub_num]
        sub_mRegions[sub_num].append(region_id)

        sinkIDs = mRegions[region_id].sinks
        sink_idxs = np.empty(sinkIDs.shape, dtype=np.uint64)
        for probe, sink_id in enumerate(sinkIDs):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)
        sink_colors = np.full(sink_idxs.shape, fill_value=sub_num, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)

    """
        Deal with islands.
    """
    cluster_flag = np.zeros((cluster_num,), dtype=np.uint8)
    scale = 1.5

    # 没有编码的岛屿聚类，则所有的岛屿聚类都合并到大陆流域
    if diClusterNum <= 0:
        for cluster_id in range(cluster_num):
            nIsland_id = clusters[cluster_id].mIsland
            attached_basin = basin[islands[nIsland_id].mSample]
            cluster_flag[cluster_id] = attached_basin
            sub_total_areas[attached_basin] += clusters[cluster_id].area
    # 如果有编码的岛屿聚类，根据距离远近合并到大陆流域或者已编码的岛屿聚类
    else:
        # 能够直接编码的岛屿聚类
        for cluster_id in diClusterIDs:
            sub_num += 1
            sub_types[sub_num] = 5
            cluster_flag[cluster_id] = sub_num
            sub_types[sub_num] = 5
            sub_areas[sub_num] = clusters[cluster_id].area
            sub_total_areas[sub_num] = sub_areas[sub_num]
        # # 未能直接编码的岛屿聚类
        # for cluster_id in range(cluster_num):
        #     if cluster_id in diClusterIDs:
        #         continue
        #     nClusterOrder = np.argmin(clusterDst[cluster_id, diClusterIDs])
        #     nClusterId = diClusterIDs[nClusterOrder]
        #     dst = clusterDst[cluster_id, nClusterId]
        #     if dst < clusters[cluster_id].distance * scale:
        #         attached_basin = cluster_flag[nClusterId]
        #     else:
        #         nIsland_id = clusters[cluster_id].mIsland
        #         attached_basin = basin[islands[nIsland_id].mSample]
        #
        #     cluster_flag[cluster_id] = attached_basin
        #     sub_total_areas[attached_basin] += clusters[cluster_id].area

        # 计算每个聚类到各编码聚类的最短距离
        nMatrix = np.zeros((cluster_num, 1 + diClusterNum), dtype=np.float32)
        for cluster_id in range(cluster_num):
            if cluster_id in diClusterIDs:
                nMatrix[cluster_id, :] = 99999999.0
                continue
            nMatrix[cluster_id, 0] = clusters[cluster_id].distance * scale
            for probe, diClusterID in enumerate(diClusterIDs, 1):
                nMatrix[cluster_id, probe] = clusterDst[cluster_id, diClusterID]

        left_cluster_num = cluster_num - diClusterNum
        while left_cluster_num > 0:
            idx = np.argmin(nMatrix)
            cluster_id, diClusterIndex = np.unravel_index(idx, nMatrix.shape)
            if diClusterIndex == 0:
                nIsland_id = clusters[cluster_id].mIsland
                attached_basin = basin[islands[nIsland_id].mSample]
            else:
                attached_basin = cluster_flag[diClusterIDs[diClusterIndex - 1]]
            cluster_flag[cluster_id] = attached_basin
            sub_total_areas[attached_basin] += clusters[cluster_id].area
            # 修改nMatrix
            nMatrix[cluster_id, :] = 99999999.0
            temp1 = nMatrix[:, diClusterIndex]
            temp2 = clusterDst[:, cluster_id]
            np.putmask(temp1, (temp2 < temp1) & (cluster_flag == 0), temp2)
            # 未处理过的岛屿聚类数量-1
            left_cluster_num -= 1

    if np.count_nonzero(cluster_flag) < cluster_num:
        raise RuntimeError("Island-cluster division failed!")

    # 绘制岛屿集合
    for cluster_id in range(cluster_num):
        attached_basin = cluster_flag[cluster_id]
        sub_clusters[attached_basin].append(cluster_id)
        clusterIslandIDs = clusters[cluster_id].islands
        iSampleIndexes = np.empty(clusterIslandIDs.shape, dtype=np.uint64)
        for probe, island_id in enumerate(clusterIslandIDs):
            iSampleIndexes[probe] = ravel_to_1dim(islands[island_id].iSample, cols)
        iSampleColors = np.full(clusterIslandIDs.shape, fill_value=attached_basin, dtype=np.uint8)
        cfunc.island_paint_uint8(iSampleIndexes, iSampleColors, dir_arr, re_dir_arr, basin)
        sub_islands[attached_basin].extend(clusterIslandIDs.tolist())

    # 绘制其他岛屿
    otherIslands = [island for island in islands.values() if island.type == 0]
    iSampleIndexes = np.empty((len(otherIslands),), dtype=np.uint64)
    iSampleColors = np.empty(iSampleIndexes.shape, dtype=np.uint8)
    for probe, island in enumerate(otherIslands):
        iSampleIndexes[probe] = ravel_to_1dim(island.iSample, cols)
        attached_basin = basin[island.mSample]
        iSampleColors[probe] = attached_basin
        island_id = island.fid
        sub_islands[attached_basin].append(island_id)
        sub_total_areas[attached_basin] += islands[island_id].area
    cfunc.island_paint_uint8(iSampleIndexes, iSampleColors, dir_arr, re_dir_arr, basin)

    # 绘制岛屿内流区
    for region_id in range(iRegionNum):
        sinkIDs = iRegions[region_id].sinks
        sink_idxs = np.empty(sinkIDs.shape, dtype=np.uint64)
        for probe, sink_id in enumerate(sinkIDs):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)

        island_id = iRegions[region_id].location
        attached_basin = basin[islands[island_id].iSample]
        sub_iRegions[attached_basin].append(region_id)

        sink_colors = np.full(sink_idxs.shape, fill_value=attached_basin, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)

    # 计算各次级流域的boundary
    cfunc.get_basin_envelopes(basin, sub_envelopes)
    head_water_code = 1

    return basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
        sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands


def divide_basin_5(src_info, root, threshold):

    # 解析工作路径
    str_src_code = str(src_info[0])
    src_folder = os.path.join(root, *str_src_code)
    src_tif = os.path.join(src_folder, str_src_code + ".tif")
    src_db = os.path.join(src_folder, str_src_code + '.db')

    # 查询流域成员信息
    basin_type, area, total_area, outlet_idx, inlet_idx, mOutletNum, mRegionNum, iRegionNum, cluster_num,\
        mOutlets, mRegions, iRegions, sinks, clusters, islands, samples, clusterDst \
        = dp.get_basin_components(src_db)
    # 从数据库中查询子流域的位置信息
    ul_offset = dp.get_ul_offset(src_db)
    # 读取当前流域的流向，汇流累积量和高程数据
    dir_arr, upa_arr, elv_arr, geo_trans, proj = \
        raster.read_tif_files(root, mRegionNum + iRegionNum, src_tif, ul_offset)

    # 判断岛屿聚类是否由一个大岛和多个小岛组成
    # 如果是，可以将大岛视作大陆，按type=4进行处理
    islandIDs = list(islands.keys())
    fIsland_id = islandIDs[0]
    fIsland_area = islands[fIsland_id].area
    if fIsland_area > total_area * 0.7 and fIsland_area > 2 * threshold:
        mOutletNum, mRegionNum, iRegionNum, cluster_num, mOutlets, mRegions, iRegions, \
            clusters, islands, samples, clusterDst = \
            prepare_4_from_5(fIsland_id, dir_arr, upa_arr, threshold, islands, iRegions)

        basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
            sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands = \
            divide_4(samples, clusterDst, mOutlets, mRegions, iRegions, sinks, clusters, islands,
                     dir_arr, upa_arr, elv_arr, cluster_num, mOutletNum, mRegionNum, iRegionNum)

    # 如果不是，则对岛屿重新进行聚类
    else:
        if cluster_num == 1:
            basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, \
                sub_outlets, sub_inlets, sub_envelopes, sub_samples, sub_mOutlets, \
                sub_mRegions, sub_iRegions, sub_clusters, sub_islands, clusters, clusterDst \
                = divide_5_1(clusterDst, iRegions, sinks, clusters, islands, dir_arr, upa_arr, iRegionNum, threshold)
        else:
            basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, \
                sub_outlets, sub_inlets, sub_envelopes, sub_samples, sub_mOutlets, \
                sub_mRegions, sub_iRegions, sub_clusters, sub_islands = \
                divide_5_2(clusterDst, iRegions, sinks, clusters, islands, dir_arr, cluster_num, iRegionNum)

    # 分割流域，并保存为新的输入
    result = break_into_sub_basins(basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas,
                                   sub_envelopes, sub_samples, sub_outlets, sub_inlets, sub_mOutlets,
                                   sub_mRegions, sub_iRegions, sub_clusters, sub_islands, clusterDst,
                                   mOutlets, mRegions, iRegions, sinks, clusters, islands,
                                   ul_offset, geo_trans, proj, threshold, root, src_info)
    return result


def prepare_4_from_5(fIslandId, dir_arr, upa_arr, threshold, islands, iRegions):

    # 准备返回数据
    new_outlets = {}
    new_mRegions = {}
    new_iRegions = {}
    new_mRegionNum = 0
    new_iRegionNum = 0
    new_clusters = {}
    new_cluster_num = 0
    new_islands = {}

    # 区分大陆边界和岛屿边界
    mainland_sample_idxs = np.array(islands[fIslandId].iSample, dtype=np.int32).reshape((-1, 2))
    all_edge, mainland_edge, island_edge = prep.diff_mainland_island(dir_arr, mainland_sample_idxs)

    # 处理大陆入海河流
    outletRecord, new_outlet_num = prep.deal_with_mainland_outlets(mainland_edge, upa_arr, threshold)
    if new_outlet_num > 0:
        new_outlets = {eid: dp.Outlet(record) for eid, record in enumerate(outletRecord)}
    del mainland_edge

    # 处理内流区
    for record in iRegions.values():
        if record.location == fIslandId:
            record.location = 0
            new_mRegions[new_mRegionNum] = record
            new_mRegionNum += 1
        else:
            new_iRegions[new_iRegionNum] = record
            new_iRegionNum += 1

    # 处理岛屿
    island_label_res, new_island_num = cfunc.label(island_edge)
    if new_island_num + 1 != len(islands):
        raise RuntimeError("Uncorrect number of islands!")
    del island_edge

    if new_island_num > 0:
        # 对岛屿按照面积进行排序
        island_area = np.zeros((new_island_num + 1,), dtype=np.float64)
        islandIDMap = np.empty((new_island_num + 1,), dtype=np.int32)
        for island_id, record in islands.items():
            new_island_id = island_label_res[record.iSample]
            if new_island_id == 0:
                island_area[new_island_id] = islands[fIslandId].area
                islandIDMap[new_island_id] = fIslandId
            else:
                island_area[new_island_id] = record.area
                islandIDMap[new_island_id] = island_id
        islandOrder = np.argsort(-island_area)
        island_area = island_area[islandOrder]
        islandIDMap = islandIDMap[islandOrder]

        # 统计岛屿的相关信息
        _, island_envelope = cfunc.island_statistic(island_label_res, new_island_num, dir_arr, upa_arr)
        rows, cols = dir_arr.shape
        island_envelope[0] = (0, 0, rows - 1, cols - 1)
        island_envelope = island_envelope[islandOrder]
        # 将大陆海岸线和岛屿海岸线合并到一个图层
        island_label_res[all_edge] += 1
        del all_edge

        # 创建RTree索引
        islandBrtSpIndex = prep.create_island_brt_spindex(island_envelope[1:])
        coastSpIndex = [prep.create_island_spindex(island_label_res, islandOrder[i] + 1, island_envelope[i])
                        for i in range(new_island_num + 1)]
        coastGeoms = [prep.create_island_geom(island_label_res, islandOrder[i] + 1, island_envelope[i])
                      for i in range(1, new_island_num + 1)]
        del island_label_res

        # 计算岛屿到大陆的距离
        mSamples, iSamples, imDst = prep.calc_island_mainland_dst(coastSpIndex, island_envelope, new_island_num)
        prep.relocate_im_sample(mSamples, new_island_num, dir_arr, upa_arr, threshold)
        # 计算岛屿之间的距离
        iiDst, accessible = prep.calc_island_island_dst(coastSpIndex, coastGeoms, islandBrtSpIndex,
                                                        island_envelope, island_area, imDst, new_island_num)
        # 岛屿聚类
        island_cluster_flag, cluster_num, clusterArea, clusterDst = \
            prep.deal_with_islands(iiDst, accessible, island_area, imDst, new_island_num)

        # 重新提取岛屿
        for i in range(1, new_island_num + 1):
            island_id = islandIDMap[i]
            record = islands[island_id]
            record.distance = float(imDst[i])
            record.mSample = tuple(mSamples[i].tolist())
            record.type = 0 if island_cluster_flag[i] == 0 else 1
            new_islands[island_id] = record

        # 重新提取岛屿聚类
        for i in range(1, cluster_num + 1):
            cluster_area = float(clusterArea[i])
            curIslandArr = np.argwhere(island_cluster_flag == i).ravel()
            nIsland_id = curIslandArr[np.argmin(imDst[curIslandArr])]
            dst = float(imDst[nIsland_id])
            nIsland_id = int(islandIDMap[nIsland_id])
            islandArr = islandIDMap[curIslandArr]
            new_clusters[new_cluster_num] = dp.Cluster((cluster_area, dst, nIsland_id, islandArr.tobytes()))
            new_cluster_num += 1
        new_clusterDst = clusterDst[1:, 1:].copy()

    else:
        new_clusterDst = None

    return new_outlet_num, new_mRegionNum, new_iRegionNum, new_cluster_num, \
        new_outlets, new_mRegions, new_iRegions, new_clusters, new_islands, mainland_sample_idxs, new_clusterDst


def divide_5_1(clusterDst, iRegions, sinks, clusters, islands, dir_arr, upa_arr, iRegionNum, threshold):
    # 初始化流域划分基本信息
    sub_types = np.zeros((11,), dtype=np.uint8)  # 子流域类型
    sub_inlets = np.zeros((11, 2), dtype=np.int32)  # 子流域入水口
    sub_outlets = np.zeros((11, 2), dtype=np.int32)  # 子流域出水口
    sub_areas = np.zeros((11,), dtype=np.float64)  # 子流域面积
    sub_total_areas = np.zeros((11,), dtype=np.float64)  # 子流域总面积
    sub_downs = np.zeros((11, ), dtype=np.uint8)
    sub_envelopes = np.zeros((11, 4), dtype=np.int32)  # 子流域外包矩形
    sub_samples = np.zeros((11, 4), dtype=np.int32)  # 子流域大陆海岸线样点
    rows, cols = dir_arr.shape
    sub_envelopes[1:, 0] = rows
    sub_envelopes[1:, 1] = cols
    sub_mOutlets = {i: [] for i in range(1, 11)}
    sub_mRegions = {i: [] for i in range(1, 11)}
    sub_iRegions = {i: [] for i in range(1, 11)}
    sub_clusters = {i: [] for i in range(1, 11)}
    sub_islands = {i: [] for i in range(1, 11)}
    basin = np.zeros((rows, cols), dtype=np.uint8)
    sub_num = 0

    island_area_threshold = threshold * 0.3
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)

    # 找到面积大于阈值的岛屿
    islandIDArr = clusters[0].islands
    for island_id in islandIDArr:
        if islands[island_id].area > island_area_threshold:
            sub_num += 1
        else:
            break
        if sub_num == 10:
            break

    # 如果没有岛屿面积较大，不进行划分
    if sub_num <= 1:
        sub_num = 1
        head_water_code = 1
        return basin, sub_num, head_water_code, sub_downs, sub_types, sub_areas, sub_total_areas, \
            sub_outlets, sub_inlets, sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, \
            sub_clusters, sub_islands, clusters, clusterDst

    # 提取岛屿边界
    island_edge = (dir_arr == 0).astype(np.uint8)
    island_label_res, new_island_num = cfunc.label(island_edge)
    if new_island_num != len(islands):
        raise RuntimeError("Uncorrect number of islands!")
    del island_edge

    # 对岛屿按照面积进行排序
    island_area = np.zeros((new_island_num + 1,), dtype=np.float64)
    islandIDMap = np.empty((new_island_num + 1,), dtype=np.int32)
    for island_id, record in islands.items():
        new_island_id = island_label_res[record.iSample]
        island_area[new_island_id] = record.area
        islandIDMap[new_island_id] = island_id
    island_area[0] = 99999999.0
    islandIDMap[0] = 0
    islandOrder = np.argsort(-island_area)
    island_area = island_area[islandOrder]
    islandIDMap = islandIDMap[islandOrder]

    # 提取岛屿外包矩形
    _, island_envelope = cfunc.island_statistic(island_label_res, new_island_num, dir_arr, upa_arr)
    island_envelope[0] = (0, 0, rows - 1, cols - 1)
    island_envelope = island_envelope[islandOrder]

    # 创建RTree索引
    coastSpIndex = [prep.create_island_spindex(island_label_res, islandOrder[i], island_envelope[i])
                    for i in range(1, new_island_num + 1)]
    coastGeoms = [prep.create_island_geom(island_label_res, islandOrder[i], island_envelope[i])
                  for i in range(1, new_island_num + 1)]
    del island_label_res

    # 计算岛屿之间的距离
    islandDstArr = np.zeros((new_island_num + 1, new_island_num + 1), dtype=np.float32)
    for i in range(1, new_island_num + 1):
        for j in range(i + 1, new_island_num + 1):
            dst = prep.calc_island_dst_3(coastSpIndex[i - 1], coastSpIndex[j - 1], island_envelope[j], coastGeoms[j-1])
            islandDstArr[i, j] = dst
            islandDstArr[j, i] = dst

    """
        重新对岛屿进行聚类
    """
    islandClusterFlag = np.zeros((new_island_num + 1,), dtype=np.uint8)
    for i in range(1, sub_num + 1):
        islandClusterFlag[i] = i

    # 合并未编码岛屿到最近的编码岛屿
    diIslandNum = sub_num
    nMatrix = np.zeros((new_island_num, diIslandNum), dtype=np.float32)
    for island_idx in range(new_island_num):
        if island_idx < diIslandNum:
            nMatrix[island_idx, :] = 99999999.0
        else:
            for probe in range(diIslandNum):
                nMatrix[island_idx, probe] = islandDstArr[island_idx + 1, probe + 1]

    left_island_num = new_island_num - diIslandNum
    while left_island_num > 0:
        idx = np.argmin(nMatrix)
        cluster_id, diClusterIndex = np.unravel_index(idx, nMatrix.shape)
        attached_basin = islandClusterFlag[diClusterIndex + 1]
        islandClusterFlag[cluster_id + 1] = attached_basin
        # 修改nMatrix
        nMatrix[cluster_id, :] = 99999999.0
        temp1 = nMatrix[:, diClusterIndex]
        temp2 = islandDstArr[1:, cluster_id + 1]
        np.putmask(temp1, (temp2 < temp1) & (islandClusterFlag[1:] == 0), temp2)
        # 未处理过的岛屿聚类数量-1
        left_island_num -= 1

    if np.count_nonzero(islandClusterFlag) < new_island_num:
        raise RuntimeError("Island-cluster division failed!")


    # for i in range(sub_num + 1, new_island_num + 1):
    #     # 挑选最近的编码岛屿
    #     temp = islandDstArr[i].ravel()
    #     attached_island = np.argmin(temp[1:sub_num + 1]) + 1
    #     islandClusterFlag[i] = islandClusterFlag[attached_island]

    """
        按照面积大小，重新分配聚类编号
    """
    # 计算cluster的面积
    new_Cluster_num = sub_num
    clusterArea = np.zeros((new_Cluster_num + 1,), dtype=np.float64)
    clusterArea[0] = 99999999.0
    for i in range(1, new_island_num + 1):
        cluster_id = islandClusterFlag[i]
        clusterArea[cluster_id] += island_area[i]

    # 对cluster按面积排序
    clusterOrder = np.argsort(-clusterArea).astype(np.int32)
    clusterArea = clusterArea[clusterOrder]
    # 修改cluster编号
    maskOrder = np.empty((new_Cluster_num + 1,), dtype=np.uint8)
    for i in range(new_Cluster_num + 1):
        maskOrder[clusterOrder[i]] = i
    np.putmask(islandClusterFlag, islandClusterFlag > 0, maskOrder[islandClusterFlag])

    new_clusterDst = np.full((new_Cluster_num + 1, new_Cluster_num + 1), fill_value=99999999.0, dtype=np.float32)
    prep.calc_cluster_dst(islandClusterFlag, islandDstArr, new_island_num, new_clusterDst)

    new_clusters = {}
    # 分配每个岛屿的编码
    for i in range(1, new_Cluster_num + 1):
        cluster_area = clusterArea[i]
        curIslandArr = np.argwhere(islandClusterFlag == i).ravel()
        islandArr = islandIDMap[curIslandArr]
        new_clusters[i - 1] = dp.Cluster((cluster_area, 99999999., 0, islandArr.tobytes()))
        sub_clusters[i].append(i - 1)

        iSampleIndexes = np.empty(islandArr.shape, dtype=np.uint64)
        for probe, island_id in enumerate(islandArr):
            iSampleIndexes[probe] = ravel_to_1dim(islands[island_id].iSample, cols)
        iSampleColors = np.full(islandArr.shape, fill_value=i, dtype=np.uint8)
        cfunc.island_paint_uint8(iSampleIndexes, iSampleColors, dir_arr, re_dir_arr, basin)
        sub_islands[i].extend(islandArr.tolist())

        sub_types[i] = 5
        sub_areas[i] = cluster_area
        sub_total_areas[i] = cluster_area

    # 绘制岛屿内流区
    for region_id in range(iRegionNum):
        sinkIDs = iRegions[region_id].sinks
        sink_idxs = np.empty(sinkIDs.shape, dtype=np.uint64)
        for probe, sink_id in enumerate(sinkIDs):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)

        island_id = iRegions[region_id].location
        attached_basin = basin[islands[island_id].iSample]
        sub_iRegions[attached_basin].append(region_id)

        sink_colors = np.full(sink_idxs.shape, fill_value=attached_basin, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)

    cfunc.get_basin_envelopes(basin, sub_envelopes)
    head_water_code = 1

    return basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
        sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands, \
        new_clusters, new_clusterDst


def divide_5_2(clusterDst, iRegions, sinks, clusters, islands, dir_arr, cluster_num, iRegionNum):
    # 初始化流域划分基本信息
    sub_types = np.zeros((11,), dtype=np.uint8)  # 子流域类型
    sub_inlets = np.zeros((11, 2), dtype=np.int32)  # 子流域入水口
    sub_outlets = np.zeros((11, 2), dtype=np.int32)  # 子流域出水口
    sub_areas = np.zeros((11,), dtype=np.float64)  # 子流域面积
    sub_total_areas = np.zeros((11,), dtype=np.float64)  # 子流域总面积
    sub_downs = np.zeros((11,), dtype=np.uint8)
    sub_envelopes = np.zeros((11, 4), dtype=np.int32)  # 子流域外包矩形
    sub_samples = np.zeros((11, 4), dtype=np.int32)  # 子流域大陆海岸线样点
    rows, cols = dir_arr.shape
    sub_envelopes[1:, 0] = rows
    sub_envelopes[1:, 1] = cols
    sub_mOutlets = {i: [] for i in range(1, 11)}
    sub_mRegions = {i: [] for i in range(1, 11)}
    sub_iRegions = {i: [] for i in range(1, 11)}
    sub_clusters = {i: [] for i in range(1, 11)}
    sub_islands = {i: [] for i in range(1, 11)}
    basin = np.zeros((rows, cols), dtype=np.uint8)
    sub_num = 0

    diClusterIDs = []
    # 如果有多个岛屿聚类，给每个岛屿聚类一个单独的编号
    # 如果有10个以上的岛屿聚类，则编码前10个岛屿聚类，其他岛屿聚类合并到最近的已编码岛屿聚类

    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    clusterFlag = np.zeros((cluster_num,), dtype=np.uint8)

    # 先编码一个最大的cluster
    sub_num += 1
    clusterFlag[0] = sub_num
    diClusterIDs.append(0)
    # 在剩下的cluster中挑选远离已编码cluster的cluster
    cluster_dst_threshold = max(prep.island_dst_threshold, math.sqrt(rows ** 2 + cols ** 2) / 4)
    # cluster_area_threshold = prep.cluster_area_threshold

    while sub_num < 10:
        farAwayClusterID = 0
        distanceSum = 0.
        targets = np.argwhere(clusterFlag != 0)
        for i in range(1, cluster_num):
            if clusterFlag[i] != 0:
                continue
            tempDstArr = clusterDst[i][targets]
            if np.all(tempDstArr > cluster_dst_threshold):
                tempDstSum = np.sum(tempDstArr)
                if tempDstSum > distanceSum:
                    farAwayClusterID = i
                    distanceSum = tempDstSum

        # 如果没有远离编码cluster的cluster, 退出循环
        if farAwayClusterID == 0:
            break
        # 如果有符合条件的cluster, 将其编码
        else:
            sub_num += 1
            clusterFlag[farAwayClusterID] = sub_num
            diClusterIDs.append(farAwayClusterID)

    for i in range(1, cluster_num):
        if sub_num >= 10:
            break
        if clusterFlag[i] == 0:
            sub_num += 1
            clusterFlag[i] = sub_num
            diClusterIDs.append(i)

    # 剩余的cluster
    # targets = np.argwhere(clusterFlag != 0)
    diClusterNum = sub_num
    nMatrix = np.zeros((cluster_num, diClusterNum), dtype=np.float32)
    for cluster_id in range(cluster_num):
        if cluster_id in diClusterIDs:
            nMatrix[cluster_id, :] = 99999999.0
            continue
        for probe, diClusterID in enumerate(diClusterIDs):
            nMatrix[cluster_id, probe] = clusterDst[cluster_id, diClusterID]

    left_cluster_num = cluster_num - diClusterNum
    while left_cluster_num > 0:
        idx = np.argmin(nMatrix)
        cluster_id, diClusterIndex = np.unravel_index(idx, nMatrix.shape)
        attached_basin = clusterFlag[diClusterIDs[diClusterIndex]]
        clusterFlag[cluster_id] = attached_basin
        # 修改nMatrix
        nMatrix[cluster_id, :] = 99999999.0
        temp1 = nMatrix[:, diClusterIndex]
        temp2 = clusterDst[:, cluster_id]
        np.putmask(temp1, (temp2 < temp1) & (clusterFlag == 0), temp2)
        # 未处理过的岛屿聚类数量-1
        left_cluster_num -= 1

    if np.count_nonzero(clusterFlag) < cluster_num:
        raise RuntimeError("Island-cluster division failed!")

    # for i in range(1, cluster_num):
    #     if clusterFlag[i] != 0:
    #         continue
    #     tempDstArr = clusterDst[i][targets]
    #     attachBasin = clusterFlag[targets[np.argmin(tempDstArr)]]
    #     clusterFlag[i] = attachBasin

    # 绘制划分结果
    for cluster_id in range(cluster_num):
        attached_basin = clusterFlag[cluster_id]
        sub_clusters[attached_basin].append(cluster_id)
        sub_areas[attached_basin] += clusters[cluster_id].area

        clusterIslandIDs = clusters[cluster_id].islands
        iSampleIndexes = np.empty(clusterIslandIDs.shape, dtype=np.uint64)
        for probe, island_id in enumerate(clusterIslandIDs):
            iSampleIndexes[probe] = ravel_to_1dim(islands[island_id].iSample, cols)
        iSampleColors = np.full(clusterIslandIDs.shape, fill_value=attached_basin, dtype=np.uint8)
        cfunc.island_paint_uint8(iSampleIndexes, iSampleColors, dir_arr, re_dir_arr, basin)
        sub_islands[attached_basin].extend(clusterIslandIDs.tolist())

    # 绘制岛屿内流区
    for region_id in range(iRegionNum):
        sinkIDs = iRegions[region_id].sinks
        sink_idxs = np.empty(sinkIDs.shape, dtype=np.uint64)
        for probe, sink_id in enumerate(sinkIDs):
            sink_idxs[probe] = ravel_to_1dim(sinks[sink_id].loc, cols)

        island_id = iRegions[region_id].location
        attached_basin = basin[islands[island_id].iSample]
        sub_iRegions[attached_basin].append(region_id)

        sink_colors = np.full(sink_idxs.shape, fill_value=attached_basin, dtype=np.uint8)
        cfunc.paint_up_uint8(sink_idxs, sink_colors, re_dir_arr, basin)

    sub_types[1:sub_num + 1] = 5
    sub_total_areas[1:sub_num + 1] = sub_areas[1:sub_num + 1]

    cfunc.get_basin_envelopes(basin, sub_envelopes)
    head_water_code = 1

    return basin, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas, sub_outlets, sub_inlets, \
        sub_envelopes, sub_samples, sub_mOutlets, sub_mRegions, sub_iRegions, sub_clusters, sub_islands


def break_into_sub_basins(basin_arr, sub_num, head_water_code, sub_types, sub_downs, sub_areas, sub_total_areas,
                          sub_envelopes, sub_samples, sub_outlets, sub_inlets, sub_mOutlets,
                          sub_mRegions, sub_iRegions, sub_clusters, sub_islands,
                          clusterDst, mOutlets, mRegions, iRegions, sinks, clusters, islands,
                          ul_offset, bench_trans, proj, min_threshold, root, src_info):

    # 编码相关信息
    cur_code = src_info[1]
    src_type = src_info[3]
    base_code = cur_code * 10
    cur_folder = os.path.join(root, *str(cur_code))
    # 返回结果
    ins_val_list = []
    #########################################
    #           如果没有划分出子流域            #
    #########################################
    if sub_num <= 1:
        ins_val = list(src_info)
        ins_val[1] = base_code
        ins_val[-1] = 0
        ins_val_list.append(tuple(ins_val))
        if src_type == 2:
            ins_val_list.append(base_code)
        return ins_val_list

    ##########################################
    #             如果划分出了子流域             #
    ##########################################
    for i in range(1, sub_num + 1):
        if sub_types[i] == 2 and -0.1 < sub_areas[i] < 0.0:
            sub_areas[i] = 0.01
            sub_total_areas[i] = 0.01

    if np.any(sub_areas < 0.0) or np.any(sub_total_areas < 0.0):
        raise RuntimeError("Area error 1!")
    if abs(np.sum(sub_total_areas) - src_info[5]) > 1.0:
        print(np.sum(sub_total_areas), src_info[5])
        raise RuntimeError("Area error 2!")

    # 准备下一层级流域划分需要的输入
    for i in range(1, sub_num + 1):
        """ 路径检查 """
        # 如果编码结果为10，则用0代替
        if i == 10:
            sub_code = base_code
            sub_folder = os.path.join(cur_folder, '0')
        else:
            sub_code = base_code + i
            sub_folder = os.path.join(cur_folder, str(i))
        # 判断次级目录是否已经存在
        if not os.path.exists(sub_folder):
            os.makedirs(sub_folder)  # 创建子流域目录

        sub_db = os.path.join(sub_folder, "%d.db" % sub_code)
        """ 裁剪至子流域 """
        # 地理参考
        min_row = int(sub_envelopes[i, 0] - 1)
        max_row = int(sub_envelopes[i, 2] + 2)
        min_col = int(sub_envelopes[i, 1] - 1)
        max_col = int(sub_envelopes[i, 3] + 2)
        sub_rows = max_row - min_row
        sub_cols = max_col - min_col
        ul_lat = bench_trans[3] + min_row * bench_trans[5]  # 左上角纬度
        ul_lon = bench_trans[0] + min_col * bench_trans[1]  # 左上角经度
        sub_trans = (ul_lon, bench_trans[1], 0, ul_lat, 0, bench_trans[5])
        trans_val = (ul_lon, bench_trans[1], 0, ul_lat, 0, bench_trans[5],
                     sub_rows, sub_cols, ul_offset[0] + min_row, ul_offset[1] + min_col)
        dp.insert_trans(sub_db, trans_val)

        """ 保存子流域栅格数据和矢量数据"""
        # 子流域掩膜矩阵
        mask = basin_arr[min_row:max_row, min_col:max_col] == i
        mask = mask.astype(np.uint8)
        # 保存子流域范围文件
        raster.output_basin_tif(sub_folder, sub_code, mask, sub_trans, proj)

        """ 初始化子流域统计信息 """
        bas_type = int(sub_types[i])
        bas_area = float(sub_areas[i])
        total_area = float(sub_total_areas[i])
        outlet_ridx = 0
        outlet_cidx = 0
        inlet_ridx = 0
        inlet_cidx = 0
        outlet_num = 0
        mRegion_num = 0
        iRegion_num = 0
        sink_num = 0
        cluster_num = 0
        island_num = 0
        samples = None
        clusterDistance = None
        divisible = 1
        outlet_lon = -9999.0
        outlet_lat = -9999.0
        inlet_lon = -9999.0
        inlet_lat = -9999.0
        down_code = 0

        if bas_type == 1:
            # flow into a downstream sub-basin
            if sub_downs[i] != 0:
                down_code = int(base_code + sub_downs[i])
            # outlet point
            outlet_ridx = int(sub_outlets[i, 0]) - min_row
            outlet_cidx = int(sub_outlets[i, 1]) - min_col
            outlet_lon = ul_lon + (outlet_cidx + 0.5) * bench_trans[1]
            outlet_lat = ul_lat + (outlet_ridx + 0.5) * bench_trans[5]
            # deal with mainland exorheic region
            mRegion_num = len(sub_mRegions[i])
            if mRegion_num > 0:
                insList = (mRegions[region_id].morph() for region_id in sub_mRegions[i])
                dp.insert_regions(sub_db, insList)
                # deal with exorheic basins of each exorheic region
                sinkIdList = [mRegions[region_id].sinks for region_id in sub_mRegions[i]]
                sinkIdArray = np.concatenate(sinkIdList, axis=0)
                sink_num = sinkIdArray.shape[0]
                insList = (sinks[sink_id].morph(min_row, min_col) for sink_id in sinkIdArray)
                dp.insert_sinks(sub_db, insList)
            if total_area < min_threshold and mRegion_num <= 0:
                divisible = 0

        elif bas_type == 2:
            # flow into a downstream sub-basin
            if sub_downs[i] != 0:
                down_code = int(base_code + sub_downs[i])
            # outlet point and inlet point
            outlet_ridx = int(sub_outlets[i, 0]) - min_row
            outlet_cidx = int(sub_outlets[i, 1]) - min_col
            inlet_ridx = int(sub_inlets[i, 0]) - min_row
            inlet_cidx = int(sub_inlets[i, 1]) - min_col
            outlet_lon = ul_lon + (outlet_cidx + 0.5) * bench_trans[1]
            outlet_lat = ul_lat + (outlet_ridx + 0.5) * bench_trans[5]
            inlet_lon = ul_lon + (inlet_cidx + 0.5) * bench_trans[1]
            inlet_lat = ul_lat + (inlet_ridx + 0.5) * bench_trans[5]

            # deal with mainland exorheic region
            mRegion_num = len(sub_mRegions[i])
            if mRegion_num > 0:
                insList = (mRegions[region_id].morph() for region_id in sub_mRegions[i])
                dp.insert_regions(sub_db, insList)
                # deal with exorheic basins of each exorheic region
                sinkIdList = [mRegions[region_id].sinks for region_id in sub_mRegions[i]]
                sinkIdArray = np.concatenate(sinkIdList, axis=0)
                sink_num = sinkIdArray.shape[0]
                insList = (sinks[sink_id].morph(min_row, min_col) for sink_id in sinkIdArray)
                dp.insert_sinks(sub_db, insList)
            if total_area < min_threshold and mRegion_num <= 0:
                divisible = 0

        elif bas_type == 3:
            # flow into an enclosed sink
            down_code = -1
            # the bottom of the sink
            sinkIdArray = mRegions[sub_mRegions[i][0]].sinks
            sink_num = sinkIdArray.shape[0]
            outlet_ridx, outlet_cidx = sinks[sinkIdArray[0]].loc
            outlet_ridx -= min_row
            outlet_cidx -= min_col
            outlet_lon = ul_lon + (outlet_cidx + 0.5) * bench_trans[1]
            outlet_lat = ul_lat + (outlet_ridx + 0.5) * bench_trans[5]

            # deal with mainland exorheic region
            mRegion_num = 1
            insList = (mRegions[region_id].morph() for region_id in sub_mRegions[i])
            dp.insert_regions(sub_db, insList)
            # deal with exorheic basins of each exorheic region
            insList = (sinks[sink_id].morph(min_row, min_col) for sink_id in sinkIdArray)
            dp.insert_sinks(sub_db, insList)
            if total_area < min_threshold and sink_num <= 1:
                divisible = 0

        elif bas_type == 4:
            # deal with mainland river estuary
            outlet_num = len(sub_mOutlets[i])
            insList = (mOutlets[outlet_id].morph(min_row, min_col) for outlet_id in sub_mOutlets[i])
            dp.insert_outlets(sub_db, insList)
            # deal with mainland coastline sample
            sample_ridx = sub_samples[i, 0] - min_row
            sample_cidx = sub_samples[i, 1] - min_col
            samples = np.array([sample_ridx, sample_cidx], dtype=np.int32).tobytes()

            # deal with exorheic region
            mRegion_num = len(sub_mRegions[i])
            iRegion_num = len(sub_iRegions[i])
            if mRegion_num + iRegion_num > 0:
                insList = [mRegions[region_id].morph() for region_id in sub_mRegions[i]]
                insList.extend(iRegions[region_id].morph() for region_id in sub_iRegions[i])
                dp.insert_regions(sub_db, insList)
                # deal with exorheic basins of each exorheic region
                sinkIdList = [mRegions[region_id].sinks for region_id in sub_mRegions[i]]
                sinkIdList.extend(iRegions[region_id].sinks for region_id in sub_iRegions[i])
                sinkIdArray = np.concatenate(sinkIdList, axis=0)
                sink_num = sinkIdArray.shape[0]
                insList = (sinks[sink_id].morph(min_row, min_col) for sink_id in sinkIdArray)
                dp.insert_sinks(sub_db, insList)

            # deal with islands
            # island cluster
            cluster_num = len(sub_clusters[i])
            if cluster_num > 0:
                insList = (clusters[cluster_id].morph() for cluster_id in sub_clusters[i])
                dp.insert_clusters(sub_db, insList)

            # deal with other islands
            island_num = len(sub_islands[i])
            if island_num > 0:
                insList = (islands[island_id].morph(min_row, min_col) for island_id in sub_islands[i])
                dp.insert_islands(sub_db, insList)

            # distances between island clusters
            sub_clusterDst = np.empty((cluster_num, cluster_num), dtype=np.float32)
            for row in range(cluster_num):
                rowClusterID = sub_clusters[i][row]
                for col in range(cluster_num):
                    colClusterID = sub_clusters[i][col]
                    sub_clusterDst[row, col] = clusterDst[rowClusterID, colClusterID]
            clusterDistance = sub_clusterDst.tobytes()

            if total_area < min_threshold and mRegion_num <= 0 and cluster_num <= 0:
                divisible = 0

        elif bas_type == 5:
            # deal with islands
            # island cluster
            cluster_num = len(sub_clusters[i])
            if cluster_num > 0:
                insList = (clusters[cluster_id].morph() for cluster_id in sub_clusters[i])
                dp.insert_clusters(sub_db, insList)

            # deal with other islands
            island_num = len(sub_islands[i])
            if island_num > 0:
                insList = (islands[island_id].morph(min_row, min_col) for island_id in sub_islands[i])
                dp.insert_islands(sub_db, insList)

            # deal with island exorheic region
            iRegion_num = len(sub_iRegions[i])
            if iRegion_num > 0:
                insList = (iRegions[region_id].morph() for region_id in sub_iRegions[i])
                dp.insert_regions(sub_db, insList)
                # deal with exorheic basins of each exorheic region
                sinkIdList = [iRegions[region_id].sinks for region_id in sub_iRegions[i]]
                sinkIdArray = np.concatenate(sinkIdList, axis=0)
                sink_num = sinkIdArray.shape[0]
                insList = (sinks[sink_id].morph(min_row, min_col) for sink_id in sinkIdArray)
                dp.insert_sinks(sub_db, insList)

            # distances between island clusters
            sub_clusterDst = np.empty((cluster_num, cluster_num), dtype=np.float32)
            for row in range(cluster_num):
                rowClusterID = sub_clusters[i][row]
                for col in range(cluster_num):
                    colClusterID = sub_clusters[i][col]
                    sub_clusterDst[row, col] = clusterDst[rowClusterID, colClusterID]
            clusterDistance = sub_clusterDst.tobytes()

            if cluster_num == 1 and total_area < min_threshold:
                divisible = 0

        else:
            pass

        insValue = (bas_type, bas_area, total_area, outlet_ridx, outlet_cidx, inlet_ridx, inlet_cidx,
                    outlet_num, mRegion_num + iRegion_num, sink_num, cluster_num, island_num,
                    samples, clusterDistance)
        dp.insert_property(sub_db, insValue)

        ins_val = (sub_code, sub_code, down_code, bas_type, bas_area, total_area, sink_num, island_num,
                   outlet_lon, outlet_lat, inlet_lon, inlet_lat, ul_lon, ul_lat, sub_cols, sub_rows,
                   bench_trans[1], bench_trans[5], divisible)
        ins_val_list.append(ins_val)

    # 插入源头流域; 仅当单前流域类型type=2时，有效
    if src_type == 2:
        ins_val_list.append(base_code + head_water_code)

    return ins_val_list
