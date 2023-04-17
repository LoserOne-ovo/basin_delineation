import os
import sys
import math
import time
import numpy as np
import argparse
sys.path.append(r"../")
import db_op as dp
import file_op as fp
from util import interface as cfunc
from util import raster
from rtree import index
from numba import jit
from osgeo import ogr


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

island_dst_scale = 1.0
island_dst_threshold = 20.0 * 2
im_dst_threshold = 20.0 * 5
island_area_threshold = 5.0
cluster_area_threshold = 30.0


def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="create property database for a basin at level 1.")
    parser.add_argument("config", help="configuration file")
    parser.add_argument("top_code", help="code of level 1 basin", type=int, choices=range(1, 10))
    parser.add_argument("predecessor", help="Predecessors", type=int, choices=[0, 1], default=0)
    args = parser.parse_args()

    p_root, level_db, min_ths = fp.parse_basin_ini(args.config)
    t_code = args.top_code
    predecessor = args.predecessor

    return p_root, level_db, min_ths, t_code, predecessor


@jit(nopython=True)
def ravel_to_1dim(idx, cols):
    return idx[0] * cols + idx[1]


@jit(nopython=True)
def distance_pp(corA, corB):
    """
    Calculate the distance between two points on a two-dimensional plane
    :param corA: point a
    :param corB: point b
    :return: distance
    """
    a2 = math.pow(corA[0] - corB[0], 2)
    b2 = math.pow(corA[1] - corB[1], 2)
    return math.sqrt(a2 + b2)


@jit(nopython=True)
def distance_pe(cor, rect):
    if cor[0] < rect[0]:
        x = rect[0]
    elif cor[0] > rect[2]:
        x = rect[2]
    else:
        x = cor[0]

    if cor[1] < rect[1]:
        y = rect[1]
    elif cor[1] > rect[3]:
        y = rect[3]
    else:
        y = cor[1]

    if cor[0] == x and cor[1] == y:
        return 0.
    else:
        return distance_pp(cor, (x, y))


@jit(nopython=True)
def distance_ee(rectA, rectB):
    if rectA[2] < rectB[0]:
        x_diff = rectB[0] - rectA[2]
    elif rectA[0] > rectB[2]:
        x_diff = rectA[0] - rectB[2]
    else:
        x_diff = 0.

    if rectA[3] < rectB[1]:
        y_diff = rectB[1] - rectA[3]
    elif rectA[1] > rectB[3]:
        y_diff = rectA[1] - rectB[3]
    else:
        y_diff = 0.

    if x_diff == 0. and y_diff == 0.:
        return 0.
    else:
        return math.sqrt(x_diff * x_diff + y_diff * y_diff)


@jit(nopython=True)
def check_up_outlets(outlet_idxs, board):
    """
    出水口的四邻域不能有出水口
    :param outlet_idxs:
    :param board:
    :return:
    """
    flag = 1
    for i, j in outlet_idxs:
        if board[i, j + 1] == 2:
            print((i, j), (i, j + 1))
            flag = 0
        if board[i + 1, j] == 2:
            print((i, j), (i + 1, j))
            flag = 0
        if board[i, j - 1] == 2:
            print((i, j), (i, j - 1))
            flag = 0
        if board[i - 1, j] == 2:
            print((i, j), (i - 1, j))
            flag = 0
    return flag


@jit(nopython=True)
def relocate_im_sample(mSamples, island_num, dir_arr, upa_arr, min_river_ths):
    for i in range(1, island_num + 1):
        loc_i, loc_j = mSamples[i]
        if upa_arr[loc_i, loc_j] > min_river_ths:
            if dir_arr[loc_i, loc_j + 1] == 0 and upa_arr[loc_i, loc_j + 1] < min_river_ths:
                loc_j = loc_j + 1
            elif dir_arr[loc_i + 1, loc_j] == 0 and upa_arr[loc_i + 1, loc_j] < min_river_ths:
                loc_i = loc_i + 1
            elif dir_arr[loc_i, loc_j - 1] == 0 and upa_arr[loc_i, loc_j - 1] < min_river_ths:
                loc_j = loc_j - 1
            elif dir_arr[loc_i - 1, loc_j] == 0 and upa_arr[loc_i - 1, loc_j] < min_river_ths:
                loc_i = loc_i - 1
            else:
                raise RuntimeError("Can't find nearest coastline!")
        mSamples[i] = (loc_i, loc_j)


@jit(nopython=True)
def get_scan_window(envelope, radius):
    return envelope[0] - radius, envelope[1] - radius, envelope[2] + radius, envelope[3] + radius


@jit(nopython=True)
def calc_cluster_dst(island_cluster_flag, islandDstArr, island_num, clusterDst):
    # 计算岛屿聚类之间的距离
    for i in range(1, island_num + 1):
        iClusterId = island_cluster_flag[i]
        if iClusterId == 0:
            continue

        for j in range(i + 1, island_num + 1):
            if islandDstArr[i, j] == 0.:
                continue
            jClusterId = island_cluster_flag[j]
            if jClusterId == 0:
                continue
            if iClusterId == jClusterId:
                continue
            if islandDstArr[i, j] < clusterDst[iClusterId, jClusterId]:
                clusterDst[iClusterId, jClusterId] = islandDstArr[i, j]
                clusterDst[jClusterId, iClusterId] = islandDstArr[i, j]


@jit(nopython=True)
def island_cluster(island_id, cluster_id, stack, queue, accessArr, cluster_flag, ndValue, island_num):
    eProbe = 1
    sProbe = 1
    stack[0] = island_id
    queue[0] = island_id
    cluster_flag[island_id] = cluster_id

    while eProbe > 0:
        eProbe -= 1
        iProbe = stack[eProbe]
        for jProbe in range(1, island_num + 1):
            if cluster_flag[jProbe] != ndValue:
                continue
            if accessArr[iProbe, jProbe] != 0 and accessArr[jProbe, iProbe] != 0:
                cluster_flag[jProbe] = cluster_id
                stack[eProbe] = jProbe
                eProbe += 1
                queue[sProbe] = jProbe
                sProbe += 1

    return sProbe


def diff_mainland_island(dir_arr, mainland_samples):
    """
    提取大陆海岸线和岛屿海岸线
    :param dir_arr:
    :param mainland_samples:
    :return:
    """
    rows, cols = dir_arr.shape
    mainland_edge = np.zeros(dir_arr.shape, dtype=np.uint8)
    mSample_num = mainland_samples.shape[0]
    if mSample_num <= 0:
        raise RuntimeError("Can't find mainland coastline!")
    mSampleIndexes = np.empty((mSample_num, ), dtype=np.uint64)
    probe = 0
    flag = True
    for ridx, cidx in mainland_samples:
        mSampleIndexes[probe] = ravel_to_1dim((int(ridx), int(cidx)), cols)
        probe += 1
        if dir_arr[ridx, cidx] != 0:
            flag = False
    if flag is False:
        raise RuntimeError("Can't find mainland coastline!")

    mSampleColors = np.full((mSample_num, ), fill_value=1, dtype=np.uint8)
    cfunc.calc_coastal_edge(mSampleIndexes, mSampleColors, dir_arr, mainland_edge)

    # 提取岛屿边界
    all_edge = (dir_arr == 0)
    island_edge = np.zeros(dir_arr.shape, dtype=np.uint8)
    np.putmask(island_edge, all_edge, 1 - mainland_edge)

    return all_edge, mainland_edge, island_edge


def deal_with_mainland_outlets(mainland_edge, upa_arr, min_river_ths):
    """

    :param mainland_edge:
    :param upa_arr:
    :param min_river_ths:
    :return:
    """

    # 提取大陆边界上的主要外流区
    temp_arr = np.zeros_like(upa_arr)
    np.copyto(temp_arr, upa_arr, where=mainland_edge.view(bool))
    mask = temp_arr > min_river_ths
    idx_list = np.argwhere(mask)

    # mainland_edge[mask] = 2
    # # 检查主要出水口是否相邻
    # if check_up_outlets(idx_list, mainland_edge) == 0:
    #     # raise RuntimeError("Find adjacent outlets.")
    #     print("Warning: adjacent outlets found!")

    outlet_num = idx_list.shape[0]
    outletArea = np.empty((outlet_num,), dtype=np.float32)
    probe = 0
    for loc_i, loc_j in idx_list:
        outletArea[probe] = upa_arr[loc_i, loc_j]
        probe += 1

    outletOrder = np.argsort(-outletArea)

    result = ((int(idx_list[idx, 0]), int(idx_list[idx, 1]), float(outletArea[idx])) for idx in outletOrder)
    return result, outlet_num


def deal_with_sinks(idxList, sink_num, dir_arr, upa_arr, exBasin):
    # 找到所有的内流区
    if sink_num > 65524:
        raise RuntimeError("Too many sinks!")
    if sink_num <= 0:
        return [], [], 0

    rows, cols = dir_arr.shape
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)

    # 追踪外流区
    cfunc.paint_up_mosaiced_int32(re_dir_arr, exBasin)

    sink_area = np.zeros((sink_num,), dtype=np.float32)
    for probe, idx in enumerate(idxList):
        sink_area[probe] = upa_arr[idx[0], idx[1]]
    sinkOrderIdxs = np.argsort(-sink_area)
    idxList = idxList[sinkOrderIdxs]
    sink_area = sink_area[sinkOrderIdxs]

    # 追踪内流区
    sink_idxs = (idxList[:, 0] * cols + idxList[:, 1]).astype(np.uint64)
    sink_colors = np.arange(start=-1, stop=-(sink_num + 1), step=-1, dtype=np.int32)
    cfunc.paint_up_int32(sink_idxs, sink_colors, re_dir_arr, exBasin)
    # 将相邻的内流区聚类，同时判断内流区是在大陆还是岛屿
    sink_union_flag, sink_merge_flag, region_num = cfunc.sink_union(sink_num, exBasin)

    sinks = [(eid + 1, float(sink_area[eid]), int(idxList[eid, 0]), int(idxList[eid, 1]))
             for eid, idx in enumerate(idxList)]

    region_area = np.zeros((region_num + 1,), dtype=np.float64)
    for i in range(0, sink_num):
        region_area[sink_union_flag[i + 1]] += sink_area[i]

    def region_generate_function(region_id):
        region_sinks = np.argwhere(sink_union_flag == region_id).ravel()
        region_island = int(sink_merge_flag[region_sinks[0]]) - 1
        area = float(region_area[region_id])
        region_sinks = region_sinks.astype(np.int32)
        return area, region_island, region_sinks.tobytes()

    regions = [region_generate_function(idx) for idx in range(1, region_num + 1)]

    return sinks, regions, region_num


def create_island_brt_spindex(island_envelope):
    def generation_func(envelopes):
        for eid, envelope in enumerate(envelopes, 1):
            yield eid, envelope, eid

    return index.Index(generation_func(island_envelope), interleaved=True,
                       properties=index.Property(leaf_capacity=1200))


def create_island_spindex(coast, label, envelope):
    def generation_func(box):
        for cor in box:
            sCor = (int(cor[0]), int(cor[1]))
            yield 0, sCor * 2, sCor

    min_row, min_col, max_row, max_col = envelope
    coast_samples = np.argwhere(coast[min_row:max_row + 1, min_col:max_col + 1] == label)
    coast_samples[:, 0] += min_row
    coast_samples[:, 1] += min_col

    return index.Index(generation_func(coast_samples), interleaved=True,
                       properties=index.Property(leaf_capacity=1200))


# def calc_island_dst(spIndexA, spIndexB, envelopeB):
#
#     # A为较大的岛屿，B为较小的岛屿，envelopeB为较小岛屿的外包矩形
#     # 如果岛屿B只有一个像元
#     if envelopeB[0] == envelopeB[2] and envelopeB[1] == envelopeB[3]:
#         sampleA = list(spIndexA.nearest(envelopeB, objects='raw'))[0]
#         sampleB = tuple(envelopeB[0:2])
#         minimumDst = distance_pp(sampleA, sampleB)
#
#     # 如果岛屿B只有一行或者一列
#     elif envelopeB[0] == envelopeB[2] or envelopeB[1] == envelopeB[3]:
#         sampleA = list(spIndexA.nearest(envelopeB, objects='raw'))[0]
#         sampleB = list(spIndexB.nearest(sampleA * 2, objects='raw'))[0]
#         minimumDst = distance_pp(sampleA, sampleB)
#
#     else:
#         minimumDst = 99999999.0
#         # 先找到岛屿A上离岛屿B外包矩形最近的岛屿点pSampleA
#         pSampleA = list(spIndexA.nearest(envelopeB, objects='raw'))[0]
#         # 再找到岛屿B上离pSampleA最近的点pSampleB
#         pSampleB = list(spIndexB.nearest(pSampleA * 2, objects='raw'))[0]
#         sampleA = pSampleA
#         sampleB = pSampleB
#         # 计算pSampleA和pSampleB之间的距离
#         pDst = distance_pp(pSampleA, pSampleB)
#
#         scan_window = get_scan_window(envelopeB, pDst)
#         pSamples = list(spIndexA.intersection(scan_window, objects='raw'))
#
#         for sample in pSamples:
#             pSampleB = list(spIndexB.nearest(sample * 2, objects='raw'))[0]
#             dst = distance_pp(sample, pSampleB)
#             if dst < minimumDst:
#                 minimumDst = dst
#                 sampleA = sample
#                 sampleB = pSampleB
#
#     return sampleA, sampleB, minimumDst


def calc_island_dst_2(spIndexA, spIndexB, envelopeB):

    # A为较大的岛屿，B为较小的岛屿，envelopeB为较小岛屿的外包矩形
    # 如果岛屿B只有一个像元
    if envelopeB[0] == envelopeB[2] and envelopeB[1] == envelopeB[3]:
        sampleA = list(spIndexA.nearest(envelopeB, objects='raw'))[0]
        sampleB = tuple(envelopeB[0:2])
        minimumDst = distance_pp(sampleA, sampleB)

    # 如果岛屿B只有一行或者一列
    elif envelopeB[0] == envelopeB[2] or envelopeB[1] == envelopeB[3]:
        sampleA = list(spIndexA.nearest(envelopeB, objects='raw'))[0]
        sampleB = list(spIndexB.nearest(sampleA * 2, objects='raw'))[0]
        minimumDst = distance_pp(sampleA, sampleB)

    else:
        # 判断岛屿A是否有一部分在岛屿外包矩形（envelopeB)的内部
        pSampleAs = list(spIndexA.intersection(envelopeB, objects='raw'))
        if len(pSampleAs) == 0:
            # 先找到岛屿A上离岛屿B外包矩形最近的岛屿点pSampleA
            pSampleA = list(spIndexA.nearest(envelopeB, objects='raw'))[0]
            # 再找到岛屿B上离pSampleA最近的点pSampleB
            pSampleB = list(spIndexB.nearest(pSampleA * 2, objects='raw'))[0]
            sampleA = pSampleA
            sampleB = pSampleB
            # 计算pSampleA和pSampleB之间的距离
            minimumDst = distance_pp(pSampleA, pSampleB)
        else:
            minimumDst = 99999999.0
            sampleA = (0, 0)
            sampleB = (0, 0)
            for pSampleA in pSampleAs:
                pSampleB = list(spIndexB.nearest(pSampleA * 2, objects='raw'))[0]
                pDst = distance_pp(pSampleA, pSampleB)
                if pDst < minimumDst:
                    minimumDst = pDst
                    sampleA = pSampleA
                    sampleB = pSampleB

        x_min, y_min, x_max, y_max = envelopeB.tolist()
        lines = [(x_min, y_min, x_min, y_max), (x_min, y_max, x_max, y_max),
                 (x_max, y_min, x_max, y_max), (x_min, y_min, x_max, y_min)]
        # 查询envelope四条边上的点
        for line in lines:
            pSamples = list(spIndexB.intersection(line, objects='raw'))
            for pSampleB in pSamples:
                pSampleA = list(spIndexA.nearest(pSampleB, objects='raw'))[0]
                pDst = distance_pp(pSampleA, pSampleB)
                if pDst < minimumDst:
                    minimumDst = pDst
                    sampleA = pSampleA
                    sampleB = pSampleB

    return sampleA, sampleB, minimumDst


def calc_island_dst_3(spIndexA, spIndexB, envelopeB, geometryB):

    # A为较大的岛屿，B为较小的岛屿，envelopeB为较小岛屿的外包矩形
    # 如果岛屿B只有一个像元
    if envelopeB[0] == envelopeB[2] and envelopeB[1] == envelopeB[3]:
        sampleA = list(spIndexA.nearest(envelopeB, objects='raw'))[0]
        sampleB = tuple(envelopeB[0:2])
        minimumDst = distance_pp(sampleA, sampleB)

    # 如果岛屿B只有一行或者一列
    elif envelopeB[0] == envelopeB[2] or envelopeB[1] == envelopeB[3]:
        sampleA = list(spIndexA.nearest(envelopeB, objects='raw'))[0]
        sampleB = list(spIndexB.nearest(sampleA * 2, objects='raw'))[0]
        minimumDst = distance_pp(sampleA, sampleB)

    else:
        # 判断岛屿A是否有一部分在岛屿外包矩形（envelopeB)的内部
        pSampleAs = list(spIndexA.intersection(envelopeB, objects='raw'))
        if len(pSampleAs) == 0:
            # 先找到岛屿A上离岛屿B外包矩形最近的岛屿点pSampleA
            pSampleA = list(spIndexA.nearest(envelopeB, objects='raw'))[0]
            # 再找到岛屿B上离pSampleA最近的点pSampleB
            pSampleB = list(spIndexB.nearest(pSampleA * 2, objects='raw'))[0]
            # 计算pSampleA和pSampleB之间的距离
            radius = distance_pp(pSampleA, pSampleB)
        else:
            pSampleA = pSampleAs[0]
            pSampleB = list(spIndexB.nearest(pSampleA * 2, objects='raw'))[0]
            radius = distance_pp(pSampleA, pSampleB)

        scan_window = get_scan_window(envelopeB, radius)
        pSamples = list(spIndexA.intersection(scan_window, objects='raw'))
        geometryA = create_geometry(pSamples)

        minimumDst = geometryB.Distance(geometryA)

    return minimumDst


def create_geometry(pts):

    mpt = ogr.Geometry(ogr.wkbMultiPoint)
    pt = ogr.Geometry(ogr.wkbPoint)
    for x, y in pts:
        pt.SetPoint_2D(0, x, y)
        mpt.AddGeometry(pt)

    return mpt


def create_island_geom(coast, label, envelope):

    min_row, min_col, max_row, max_col = envelope
    coast_samples = np.argwhere(coast[min_row:max_row + 1, min_col:max_col + 1] == label)
    coast_samples[:, 0] += min_row
    coast_samples[:, 1] += min_col

    pts = (sample.tolist() for sample in coast_samples)
    geom = create_geometry(pts)
    return geom


def calc_island_mainland_dst(coast, island_envelope, island_num):
    mDstSamples = np.zeros((island_num + 1, 2), dtype=np.int32)
    iDstSamples = np.zeros((island_num + 1, 2), dtype=np.int32)
    imDst = np.zeros((island_num + 1,), dtype=np.float32)

    for i in range(1, island_num + 1):
        mDstSamples[i], iDstSamples[i], imDst[i] = calc_island_dst_2(coast[0], coast[i], island_envelope[i])

    return mDstSamples, iDstSamples, imDst


def calc_island_island_dst(coastSpIndex, coastGeoms, islandBrtSpIndex, island_envelope, island_area, imDst, island_num):
    # cluster islands
    accessible = np.zeros((island_num + 1, island_num + 1), dtype=np.uint8)
    islandDstArr = np.zeros((island_num + 1, island_num + 1), dtype=np.float32)

    # Start from larger islands
    for idx in range(1, island_num + 1):
        # scan radius
        scanRadius = imDst[idx]
        scanBox = get_scan_window(island_envelope[idx], scanRadius)
        # 先模糊查询可能在扫描半径内的岛屿
        pIslands = list(islandBrtSpIndex.intersection(scanBox, objects='raw'))
        # 计算与各个岛屿之间的距离
        for island_id in pIslands:
            # 如果已经计算过两个岛屿之间的距离，则跳过该次计算
            if islandDstArr[idx, island_id] != 0 or idx == island_id:
                continue
            # 计算岛屿之间的距离
            if idx > island_id:
                dst = calc_island_dst_3(coastSpIndex[idx], coastSpIndex[island_id], island_envelope[island_id],
                                        coastGeoms[island_id - 1])
            else:
                dst = calc_island_dst_3(coastSpIndex[island_id], coastSpIndex[idx], island_envelope[idx],
                                        coastGeoms[idx - 1])
            # 存储岛屿之间的距离
            islandDstArr[idx, island_id] = dst
            islandDstArr[island_id, idx] = dst
            # 离大陆近的小岛屿的聚类半径更小
            dst_threshold = island_dst_threshold if island_area[idx] > island_area_threshold \
                else min(imDst[idx] + 1, island_dst_threshold)
            if dst < dst_threshold:
                accessible[idx, island_id] = 1
            dst_threshold = island_dst_threshold if island_area[island_id] > island_area_threshold \
                else min(imDst[island_id] + 1, island_dst_threshold)
            if dst < dst_threshold:
                accessible[island_id, idx] = 1

    return islandDstArr, accessible


def deal_with_islands(islandDstArr, accessible, island_area, imDst, island_num):

    # initialize cluster result
    noData = -(island_num + 1)
    island_cluster_flag = np.full((island_num + 1,), fill_value=noData, dtype=np.int32)
    island_cluster_flag[0] = 0

    cluster_num = 0
    clusterArea = np.zeros((island_num + 1,), dtype=np.float64)
    queue = np.empty((island_num + 1,), dtype=np.int32)
    stack = np.empty((island_num + 1,), dtype=np.int32)

    # Start from larger islands
    for idx in range(1, island_num + 1):
        # 如果这个岛屿还没被聚类，以此为聚类中心
        if island_cluster_flag[idx] == noData:
            new_cluster_flag = island_cluster_flag.copy()
            cluster_island_num = island_cluster(idx, cluster_num, stack, queue, accessible,
                                                new_cluster_flag, noData, island_num)
            # 计算面积，和距离大陆最远的距离
            cluster_area = 0.0
            cluster_maxDst = 0.0
            for i in range(0, cluster_island_num):
                island_id = queue[i]
                cluster_area += island_area[island_id]
                cluster_maxDst = max(cluster_maxDst, imDst[island_id])
            # 如果面积和距离小于阈值，则判定为其他岛屿
            if cluster_area < cluster_area_threshold and cluster_maxDst < island_dst_threshold:
                for i in range(0, cluster_island_num):
                    island_cluster_flag[queue[i]] = 0
            else:
                cluster_num += 1
                clusterArea[cluster_num] = cluster_area
                for i in range(0, cluster_island_num):
                    island_cluster_flag[queue[i]] = cluster_num

    # 对cluster按面积排序
    clusterArea[0] = 99999999.0
    clusterArea = clusterArea[0:cluster_num + 1].copy()
    clusterOrder = np.argsort(-clusterArea).astype(np.int32)
    clusterArea = clusterArea[clusterOrder]
    # 修改cluster编号
    maskOrder = np.empty((cluster_num + 1,), dtype=np.int32)
    for i in range(cluster_num + 1):
        maskOrder[clusterOrder[i]] = i
    np.putmask(island_cluster_flag, island_cluster_flag > 0, maskOrder[island_cluster_flag])

    clusterDst = np.full((cluster_num + 1, cluster_num + 1), fill_value=99999999.0, dtype=np.float32)
    calc_cluster_dst(island_cluster_flag, islandDstArr, island_num, clusterDst)

    return island_cluster_flag, cluster_num, clusterArea, clusterDst


# 默认第一层级是大陆和岛屿的混合， 对应type=4
def basin_preprocess_4(root, level_db, min_river_ths, code):
    """
    对 type=4 的第一层级流域进行处理，计算相关属性，
    使之能按照流域划分方法，被划分为若干个子流域。
    :param root: 项目的根目录
    :param level_db: 流域信息汇总数据库
    :param min_river_ths: 河网阈值
    :param code: 第一层级流域编码
    :return: None
    """
    ############################
    #        读取栅格数据        #
    ############################
    # 获取流域工作路径
    raster_folder = os.path.join(root, "raster")
    work_folder = os.path.join(root, *str(code))
    db_path = os.path.join(work_folder, "%d.db" % code)
    mainland_sample_shp = os.path.join(raster_folder, "%d_samples.shp" % code)
    # 读取流向和汇流累积量数据
    mask_tif = os.path.join(work_folder, "%d.tif" % code)

    # 从数据库中查询子流域的位置信息
    ul_offset = dp.get_ul_offset(db_path)
    # 读取当前流域的流向，汇流累积量和高程数据
    dir_arr, upa_arr, elv_arr, geo_trans, proj = raster.read_tif_files(root, 0, mask_tif, ul_offset)
    rows, cols = dir_arr.shape
    print("Data loaded at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    #######################################
    #        区分大陆海岸线和岛屿海岸线        #
    #######################################
    # 提取大陆边界的采样点,
    # 使用shapefile作为输入
    mainland_sample_idxs = raster.get_mainland_samples(mainland_sample_shp, geo_trans)
    mainland_sample_idxs = np.array(mainland_sample_idxs, dtype=np.int32)
    # 区分大陆边界和岛屿边界
    all_edge, mainland_edge, island_edge = diff_mainland_island(dir_arr, mainland_sample_idxs)
    # 计算大陆外流区的面积
    mainland_basin_area = cfunc.calc_coastal_basin_area(mainland_edge, 1, upa_arr)
    out_drainage_area = float(mainland_basin_area[1])
    total_area = out_drainage_area
    print("Coastline finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    ##########################################################
    #         look for estuaries at mainland coastline       #
    ##########################################################
    outlets, outlet_num = deal_with_mainland_outlets(mainland_edge, upa_arr, min_river_ths)
    dp.insert_outlets(db_path, outlets)
    print("Exorheic num: %d, finished at %s" %
          (outlet_num, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
    del mainland_edge

    ###################################
    #        Label all islands        #
    ###################################
    # 对岛屿进行四连通域分析，
    island_label_res, island_num = cfunc.label(island_edge)
    # 统计岛屿的相关信息
    island_area, island_envelope = cfunc.island_statistic(island_label_res, island_num, dir_arr, upa_arr)
    island_area[0] = 99999999.0
    island_envelope[0] = (0, 0, rows - 1, cols - 1)
    # 将大陆海岸线和岛屿海岸线合并到一个图层
    island_label_res[all_edge] += 1
    print("Island num: %d, finished at %s" %
          (island_num, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
    del island_edge

    ############################################
    #        Merge and locate all sinks        #
    ############################################
    sinkList = np.argwhere(dir_arr == 255)
    sink_num = sinkList.shape[0]
    sinks, regions, region_num = deal_with_sinks(sinkList, sink_num, dir_arr, upa_arr, island_label_res)
    ####################################################################
    #        Update island area with sinks located in an island        #
    ####################################################################
    for record in regions:
        location = record[1]
        if location > 0:
            island_area[location] += record[0]
        else:
            total_area += record[0]
    total_area += np.sum(island_area[1:])
    ########################################
    #        按照面积重新对岛屿进行排序         #
    ########################################
    islandOrder = np.argsort(-island_area)
    island_envelope = island_envelope[islandOrder]
    island_area = island_area[islandOrder]

    # 重新给内流区所属的岛屿赋编号
    new_regions = []
    for record in regions:
        src_island_id = record[1]
        if src_island_id > 0:
            new_island_id = np.argwhere(islandOrder == src_island_id).ravel()[0]
            temp = list(record)
            temp[1] = int(new_island_id)
            new_regions.append(tuple(temp))
        else:
            new_regions.append(record)
    # 内流区入库
    if sink_num > 0:
        dp.insert_sinks(db_path, sinks)
        dp.insert_regions(db_path, new_regions)
    print("Endorheic num: %d, region num: %d, finished at %s." %
          (sink_num, region_num, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))

    #########################################
    #        Create Rtree for island        #
    #########################################
    islandBrtSpIndex = create_island_brt_spindex(island_envelope[1:])
    island_label_res[~all_edge] = 0
    coastSpIndex = [create_island_spindex(island_label_res, islandOrder[i] + 1, island_envelope[i])
                    for i in range(island_num + 1)]
    coastGeoms = [create_island_geom(island_label_res, islandOrder[i] + 1, island_envelope[i])
                  for i in range(1, island_num + 1)]
    print("Rtree finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    del island_label_res, all_edge

    ########################################################################
    #        Calculate the distance from the island to the mainland        #
    ########################################################################
    mSamples, iSamples, imDst = calc_island_mainland_dst(coastSpIndex, island_envelope, island_num)
    relocate_im_sample(mSamples, island_num, dir_arr, upa_arr, min_river_ths)
    print("Island-mainland dist finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    del dir_arr, upa_arr

    ###################################################################
    #        Calculate the distance from  island to the island        #
    ###################################################################
    iiDst, accessible = calc_island_island_dst(coastSpIndex, coastGeoms, islandBrtSpIndex, island_envelope,
                                               island_area, imDst, island_num)
    # 输出完成时间
    print("Island-island dist finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    ################################
    #        Island cluster        #
    ################################
    island_cluster_flag, cluster_num, clusterArea, clusterDst = \
        deal_with_islands(iiDst, accessible, island_area, imDst, island_num)
    print("Island cluster finished at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    ##########################################
    #        Store island information        #
    ##########################################
    def island_generation(island_id):
        area = float(island_area[island_id])
        dst = float(imDst[island_id])
        iSample_ridx, iSample_cidx = iSamples[island_id].tolist()
        mSample_ridx, mSample_cidx = mSamples[island_id].tolist()
        itype = 0 if island_cluster_flag[island_id] == 0 else 1
        return island_id, area, dst, iSample_ridx, iSample_cidx, mSample_ridx, mSample_cidx, itype

    if island_num > 0:
        islands = (island_generation(i) for i in range(1, island_num + 1))
        dp.insert_islands(db_path, islands)

    ##################################################
    #        Store island cluster information        #
    ##################################################
    def cluster_generation(cluster_id):
        islandList = np.argwhere(island_cluster_flag == cluster_id).ravel()
        area = float(clusterArea[cluster_id])
        nIsland_id = int(islandList[np.argmin(imDst[islandList])])
        dst = float(imDst[nIsland_id])
        islandList = islandList.astype(np.int32).tobytes()
        return area, dst, nIsland_id, islandList

    if cluster_num > 0:
        clusters = (cluster_generation(i) for i in range(1, cluster_num + 1))
        dp.insert_clusters(db_path, clusters)

    ######################################
    #        Store basin property        #
    ######################################
    propertyValue = (4, float(out_drainage_area), float(total_area), 0, 0, 0, 0,
                     outlet_num, region_num, sink_num, int(cluster_num),
                     island_num, mainland_sample_idxs.astype(np.int32).tobytes(),
                     clusterDst[1:, 1:].tobytes())
    dp.insert_property(db_path, propertyValue)

    ###############################################
    #        Store level basin information        #
    ###############################################
    sumValue = [(code, code, 0, 4, float(out_drainage_area), float(total_area), sink_num, island_num,
                 -9999.0, -9999.0, -9999.0, -9999.0,
                 geo_trans[0], geo_trans[1], geo_trans[3], geo_trans[5], rows, cols, 1)]

    dp.create_level_table(level_db, 1)
    dp.insert_basin_stat(level_db, 1, sumValue)


def mask_basin(root, code):

    ############################
    #        读取栅格数据        #
    ############################
    # 获取流域工作路径
    raster_folder = os.path.join(root, "raster")
    work_folder = os.path.join(root, *str(code))
    db_path = os.path.join(work_folder, "%d.db" % code)

    # 读取流向和汇流累积量数据
    dir_tif = os.path.join(raster_folder, "dir.tif")
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif)

    # 对数据进行裁剪
    basin_envelopes = np.zeros((11, 4), dtype=np.int32)
    basin_envelopes[1:, 0] = dir_arr.shape[0]
    basin_envelopes[1:, 1] = dir_arr.shape[1]
    mask = np.zeros(dir_arr.shape, dtype=np.uint8)
    mask[dir_arr != raster.dir_nodata] = 1
    cfunc.get_basin_envelopes(mask, basin_envelopes)
    min_row = int(basin_envelopes[1, 0] - 1)
    max_row = int(basin_envelopes[1, 2] + 2)
    min_col = int(basin_envelopes[1, 1] - 1)
    max_col = int(basin_envelopes[1, 3] + 2)
    sub_rows = max_row - min_row
    sub_cols = max_col - min_col

    ul_lat = geo_trans[3] + min_row * geo_trans[5]  # 左上角纬度
    ul_lon = geo_trans[0] + min_col * geo_trans[1]  # 左上角经度
    sub_trans = (ul_lon, geo_trans[1], 0, ul_lat, 0, geo_trans[5])
    trans_val = (ul_lon, geo_trans[1], 0, ul_lat, 0, geo_trans[5],
                 sub_rows, sub_cols, 0 + min_row, 0 + min_col)
    dp.insert_trans(db_path, trans_val)
    # 裁剪栅格
    mask = mask[min_row:max_row, min_col:max_col]

    # 输出掩膜
    raster.output_basin_tif(work_folder, code, mask, sub_trans, proj)
    print("Data clipped at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))


def main():

    # 解析参数
    project_root, level_database, minimum_river_threshold, top_code, predecessor = create_args()

    time_start = time.time()
    print("Mission started at %s" % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_start)))

    if predecessor == 0:
        mask_basin(project_root, top_code)

    # 业务函数
    basin_preprocess_4(project_root, level_database, minimum_river_threshold, top_code)

    time_end = time.time()
    time_consumption = time_end - time_start
    print("Mission finished at %s." % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_end)),
          "Total time consumption: %.2f " % time_consumption)


if __name__ == "__main__":
    main()
