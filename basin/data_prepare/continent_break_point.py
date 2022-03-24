import os
import sys
sys.path.append(r"../../")
import argparse
import numpy as np
from util import raster
from util import interface as cfunc
from osgeo import ogr


def create_args():

    parser = argparse.ArgumentParser(description="Remove outlets in another continent.")
    parser.add_argument("point_shp", help="point shapefile")
    parser.add_argument("input_dir", help="input dir .tif")

    return parser.parse_args()


def get_point_cor(shp_fn):
    """
    读取点坐标的经纬度
    :param shp_fn:
    :return:
    """

    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.Open(shp_fn, 0)
    layer = ds.GetLayer()
    layer_geom_type = layer.GetGeomType()
    if layer_geom_type != 1:
        raise IOError("The geometry type of %s must be point!" % shp_fn)


    # 先读取分界点
    layer.SetAttributeFilter("type=1")
    break_point_num = layer.GetFeatureCount()
    if break_point_num < 1:
        raise IOError("No break point between two continents in %s" % shp_fn)

    break_point_list = []
    for feature in layer:
        break_point_geom = feature.GetGeometryRef()
        break_point_lon = break_point_geom.GetX(0)
        break_point_lat = break_point_geom.GetY(0)
        break_point_list.append((break_point_lon, break_point_lat))

    # 再读取要去除的大陆边界点
    layer.SetAttributeFilter("type=2")
    mask_point_num = layer.GetFeatureCount()
    if mask_point_num < 1:
        raise IOError("No mask point between two continents in %s" % shp_fn)

    mask_point_list = []
    for feature in layer:
        mask_point_geom = feature.GetGeometryRef()
        mask_point_lon = mask_point_geom.GetX(0)
        mask_point_lat = mask_point_geom.GetY(0)
        mask_point_list.append((mask_point_lon, mask_point_lat))

    return break_point_list, mask_point_list


def main(shp_fn, iDirfn):
    """

    :param shp_fn:
    :param iDirfn:
    :return:
    """
    # 读取流向栅格数据
    dir_arr, geo_trans, proj = raster.read_single_tif(iDirfn)
    rows, cols = dir_arr.shape

    # 读取点坐标
    break_points, mask_points = get_point_cor(shp_fn)

    # 将经纬度坐标转换为行列索引
    break_idxs = raster.cor2idx_list(break_points, geo_trans)
    # 检查这些点是否符合要求
    flag = True
    p = 0
    for ridx, cidx in break_idxs:
        if ridx < 0 or ridx >= rows or cidx < 0 or cidx >= cols:
            print("Point(%.4f, %.4f) is out of the extent of the input dir .tif!"
                  % (break_points[p][0], break_points[p][1]))
            flag = False
        elif dir_arr[ridx, cidx] != 0:
            print("Point(%.4f, %.4f) does not locate at the coastline!"
                  % (break_points[p][0], break_points[p][1]))
            flag = False
        else:
            pass
        p += 1
    if flag is False:
        raise RuntimeError("There is some break point invalid!")

    # 检查这些点是否符合要求
    mask_idxs = raster.cor2idx_list(mask_points, geo_trans)
    flag = True
    p = 0
    for ridx, cidx in mask_idxs:
        if ridx < 0 or ridx >= rows or cidx < 0 or cidx >= cols:
            print("Point(%.4f, %.4f) is out of the extent of the input dir .tif!"
                  % (mask_points[p][0], mask_points[p][1]))
            flag = False
        elif dir_arr[ridx, cidx] != 0:
            print("Point(%.4f, %.4f) does not locate at the coastline!"
                  % (mask_points[p][0], mask_points[p][1]))
            flag = False
        else:
            pass
        p += 1
    if flag is False:
        raise RuntimeError("There is some mask point invalid!")

    # 在break point处打断海岸线
    all_edge = np.zeros(dir_arr.shape, dtype=np.uint8)
    all_edge[dir_arr == 0] = 1
    for ridx, cidx in break_idxs:
        all_edge[ridx, cidx] = 0

    # 四连通标记海岸线
    label_res, label_num = cfunc.label(all_edge)

    # 去除不属于当前第一级流域范围的海岸线
    mask_label = [label_res[ridx, cidx] for ridx, cidx in mask_idxs]
    mask_label = np.array(mask_label, dtype=np.uint32)
    uniq_mask_label = np.unique(mask_label)
    for m_label in uniq_mask_label:
        dir_arr[label_res == m_label] = raster.dir_nodata

    # 保存
    dir_tif_name = os.path.basename(iDirfn)
    prefix, suffix = os.path.splitext(dir_tif_name)
    out_name = prefix + "_cb"  + suffix
    oDirfn = os.path.join(os.path.dirname(shp_fn), out_name)
    raster.array2tif(oDirfn, dir_arr, geo_trans, proj, nd_value=raster.dir_nodata, dtype=raster.OType.Byte)


if __name__ == "__main__":

    args = create_args()
    main(args.point_shp, args.input_dir)
