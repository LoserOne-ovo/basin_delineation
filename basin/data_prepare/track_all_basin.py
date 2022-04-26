import sys
sys.path.append(r"../../")
import numpy as np
from util import raster
from util import interface as cfunc
from osgeo import ogr, osr


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
            print("%d of %d" % (i, point_num))
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


def sink_bottom_to_shp(dir_tif, out_shp):

    # 读取流向栅格数据
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif)
    # 提取所有的内流区终点
    sink_bottom_idxs = np.argwhere(dir_arr == 255)
    # 计算所有内流区终点的经纬度
    sink_bottom_cors = [idx2cor(ridx, cidx, geo_trans) for ridx, cidx in sink_bottom_idxs]

    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.CreateDataSource(out_shp)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    layer = ds.CreateLayer("sink_bottom", srs=srs, geom_type=ogr.wkbPoint)
    FieldDefn = ogr.FieldDefn("ridx", ogr.OFTInteger)
    layer.CreateField(FieldDefn)
    FieldDefn = ogr.FieldDefn("cidx", ogr.OFTInteger)
    layer.CreateField(FieldDefn)
    featureDefn = layer.GetLayerDefn()

    for i in range(len(sink_bottom_cors)):
        lon, lat = sink_bottom_cors[i]
        ridx, cidx = sink_bottom_idxs[i]
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint(lon, lat)
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(geom)
        feature.SetField("ridx", int(ridx))
        feature.SetField("cidx", int(cidx))
        layer.CreateFeature(feature)
        
    layer.SyncToDisk()
    ds.Destroy()


def track_basin(dir_tif, in_shp, out_tif):

    ds = ogr.Open(in_shp)
    layer = ds.GetLayer()
    point_num = layer.GetFeatureCount()
    
    probe = 0
    within_sb_idxs = np.empty((point_num, 2), dtype=np.uint64)
    for feature in layer:
        within_sb_idxs[probe, 0] = feature.GetField("ridx")
        within_sb_idxs[probe, 1] = feature.GetField("cidx")
        probe += 1
    ds.Destroy()

    # 读取流向栅格数据
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif)
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


def modify_sink(in_shp, dir_tif, src_track, upd_track, upd_value):

    
    ds = ogr.Open(in_shp)
    layer = ds.GetLayer()
    point_list = []
    for feature in layer:
        point = feature.GetGeometryRef()
        lon = point.GetX()
        lat = point.GetY()
        point_list.append((lon, lat))
    ds.Destroy()

    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif)
    modify_idxs = raster.cor2idx_list(point_list, geo_trans)
    modify_idxs = np.array(modify_idxs, dtype=np.uint64)
    paint_idxs = modify_idxs[:, 0] * dir_arr.shape[1] + modify_idxs[:, 1]
    all_colors = np.empty(shape=(paint_idxs.shape[0], ), dtype=np.uint8)
    all_colors[:] = upd_value
    # 追踪上游
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    mask_arr, _, _ = raster.read_single_tif(src_track)
    cfunc.paint_up_uint8(paint_idxs, all_colors, re_dir_arr, mask_arr)

    # 输出结果栅格文件
    raster.array2tif(upd_track, mask_arr, geo_trans, proj, nd_value=0, dtype=1)


if __name__ == "__main__":


    basin_shp = r"E:\qyf\data\Europe\shp\hybas_eu_lev01_v1c.shp"
    dir_fn = r"E:\qyf\data\Europe\merge\Europe_clip_dir_1_cb.tif"
    out_fn = r"E:\qyf\data\Europe\merge\Europe_dir_track.tif"
    output_sb_shp = r"E:\qyf\data\Europe\shp\out_sb.shp"
    input_sb_shp = r"E:\qyf\data\Europe\shp\in_sb.shp"
    modify_shp = r"E:\qyf\data\Europe\shp\modify.shp"
    modify_fn = r"E:\qyf\data\Europe\merge\Europe_dir_track_1.tif"



    # sink_bottom_to_shp(dir_fn, output_sb_shp)
    # track_basin(dir_fn, input_sb_shp, out_fn)
    modify_sink(modify_shp, dir_fn, out_fn, modify_fn, 1)

    # main(basin_shp, dir_fn, out_fn)






