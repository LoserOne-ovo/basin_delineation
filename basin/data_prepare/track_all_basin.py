import sys
sys.path.append(r"../../")
import numpy as np
from util import raster
from util import interface as cfunc
from osgeo import ogr


# 矩阵索引转经纬度
def idx2cor(loc_i, loc_j, trans):
    lon = trans[0] + (loc_j + 0.5) * trans[1]
    lat = trans[3] + (loc_i + 0.5) * trans[5]
    return (lon, lat)


def get_point_within_shp(shp_fn, cor_list, idx_arr):

    # 创建numpy数组，标记当前点是否在多边形内部
    point_num = idx_arr.shape[0]
    within_flag = np.zeros(shape=(point_num, ), dtype=bool)

    # 读取多边形数据
    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.Open(shp_fn, 0)
    layer = ds.GetLayer(0)
    layer_type = layer.GetGeomType()
    if layer_type not in [3, 6]:
        raise RuntimeError("Shapefile should be polygon or multipolygon!")

    for feature in layer:
        geom = feature.GetGeometryRef()   
        for i in range(point_num):
            print(i)
            if within_flag[i] == 0:
                p_geom = ogr.Geometry(ogr.wkbPoint)
                p_geom.AddPoint(cor_list[i][0], cor_list[i][1])
                if geom.Contains(p_geom):
                    within_flag[i] = 1

    # 统计所有范围内的内流区终点
    within_idx_num = np.sum(within_flag == True)
    within_idxs = np.zeros((within_idx_num, 2), dtype=np.int32)
    p = 0
    for i in range(point_num):
        if within_flag[i] == 1:
            within_idxs[p] = idx_arr[i]
            p += 1
            
    return within_idxs


def main(bound_shp, dir_tif, out_tif):

    # 读取流向栅格数据
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif)

    # 提取所有的内流区终点
    sink_bottom_idxs = np.argwhere(dir_arr == 255)

    # 计算所有内流区终点的经纬度
    sink_bottom_cors = [idx2cor(ridx, cidx, geo_trans) for ridx, cidx in sink_bottom_idxs]
    # 计算所有位于多边形内部的内流区终点
    within_sb_idxs = get_point_within_shp(bound_shp, sink_bottom_cors, sink_bottom_idxs)

    # # 可以保存内流区终点索引，避免再做一次空间分析
    # # np.save(r"temp.npy", within_sb_idxs)
    # within_sb_idxs = np.load(r"temp.npy")
    
    # 提取所有的外流区终点
    edge_idxs = np.argwhere(dir_arr == 0)

    # 合并所有的流域终点
    all_idxs = np.concatenate((within_sb_idxs, edge_idxs), axis=0).astype(np.uint64)
    paint_idxs = all_idxs[:, 0] * dir_arr.shape[1] + all_idxs[:, 1]
    all_colors = np.ones(shape=(all_idxs.shape[0], ), dtype=np.uint8)
    # 追踪上游
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    mask_arr = np.zeros(shape=dir_arr.shape, dtype=np.uint8)
    cfunc.paint_up_uint8(paint_idxs, all_colors, re_dir_arr, mask_arr)

    # 输出结果栅格文件
    raster.array2tif(out_tif, mask_arr, geo_trans, proj, nd_value=0, dtype=1)

    return 1


if __name__ == "__main__":


    basin_shp = r"E:\qyf\data\Asia\shp\hybas_as_lev01_v1c.shp"
    dir_fn = r"E:\qyf\data\Asia\merge\Asia_mask_dir_merge.tif"
    out_fn = r"E:\qyf\data\Asia\merge\Asia_dir_track.tif"

    main(basin_shp, dir_fn, out_fn)






