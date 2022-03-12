import os
import sys
sys.path.append(r"../../")
import getopt
import numpy as np
from util import raster
from osgeo import ogr


dir_no_data = 247


def mask_above_or_below(line_shp_fn, dir_tif_fn, method=1):
    """

    :param line_shp_fn:
    :param dir_tif_fn:
    :param method:
    :return:
    """

    # 读取栅格数据和辅助线数据
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif_fn)
    linestring = get_points(line_shp_fn)

    # 计算流向栅格数据的地理范围
    rows, cols = dir_arr.shape
    ul_x, delta_x, r_x, ul_y, r_y, delta_y = geo_trans
    envelope = (ul_x, ul_x + delta_x * cols, ul_y, ul_y + delta_y * rows)

    # 初始化分界线，每一列都有一个分界点，分界点之上或之下的部分设为空值
    bound_line = np.zeros((cols,), dtype=np.int32)


    pre_point_loc = None
    for lon, lat in linestring:
        # 只计算落在栅格影响范围内的点
        if check_in_envelope(lon, lat, envelope):
            loc_x = int((lon - ul_x) / delta_x)
            loc_y = int((lat - ul_y) / delta_y)
            # 如果这是第一个落在栅格影像范围内的点，那么左侧每一列的分界点都与当前落点相同
            if pre_point_loc is None:
                bound_line[0: loc_x] = loc_y
            # 如果不是，则线性插值当前落点和前一个落点之间，每一列的分界点
            else:
                delta_height = loc_y - pre_point_loc[1]
                delta_width = loc_x - pre_point_loc[0]
                for i in range(pre_point_loc[0], loc_x):
                    bound_line[i] = pre_point_loc[1] + int(((i - pre_point_loc[0]) / delta_width) * delta_height)
            # 更新前一个落点
            pre_point_loc = (loc_x, loc_y)

    # 以最后一个落在栅格影像范围内的点为准，补足剩余的分界点
    if pre_point_loc[0] < cols:
        bound_line[pre_point_loc[0]:] = pre_point_loc[1]

    # 如果保留上半部分
    if method == 1:
        for i in range(cols):
            dir_arr[bound_line[i]:, i] = dir_no_data
    else:
        for i in range(cols):
            dir_arr[0:bound_line[i], i] = dir_no_data

    # 获取流向栅格文件的文件名，并生成输出栅格的文件名
    dir_tif_name = os.path.basename(dir_tif_fn)
    prefix, suffix = os.path.splitext(dir_tif_name)
    out_name = prefix + "_mask%d" % method + suffix
    out_fn = os.path.join(os.path.dirname(line_shp_fn), out_name)
    raster.array2tif(out_fn, dir_arr, geo_trans, proj, nd_value=dir_no_data, dtype=1)

    return 1


def mask_left_or_right(line_shp_fn, dir_tif_fn, method=3):
    """

    :param line_shp_fn:
    :param dir_tif_fn:
    :param method:
    :return:
    """

    # 读取栅格数据和辅助线数据
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif_fn)
    linestring = get_points(line_shp_fn)

    # 计算流向栅格数据的地理范围
    rows, cols = dir_arr.shape
    ul_x, delta_x, r_x, ul_y, r_y, delta_y = geo_trans
    envelope = (ul_x, ul_x + delta_x * cols, ul_y, ul_y + delta_y * rows)

    # 初始化分界线，每一列都有一个分界点，分界点之上或之下的部分设为空值
    bound_line = np.zeros((rows,), dtype=np.int32)

    pre_point_loc = None
    for lon, lat in linestring:
        # 只计算落在栅格影响范围内的点
        if check_in_envelope(lon, lat, envelope):
            loc_x = int((lon - ul_x) / delta_x)
            loc_y = int((lat - ul_y) / delta_y)
            # 如果这是第一个落在栅格影像范围内的点，那么左侧每一列的分界点都与当前落点相同
            if pre_point_loc is None:
                bound_line[0: loc_y] = loc_x
            # 如果不是，则线性插值当前落点和前一个落点之间，每一列的分界点
            else:
                delta_height = loc_y - pre_point_loc[1]
                delta_width = loc_x - pre_point_loc[0]
                for i in range(pre_point_loc[1], loc_y):
                    bound_line[i] = pre_point_loc[0] + int(((i - pre_point_loc[1]) / delta_height) * delta_width)
            # 更新前一个落点
            pre_point_loc = (loc_x, loc_y)

    # 以最后一个落在栅格影像范围内的点为准，补足剩余的分界点
    if pre_point_loc[1] < rows:
        bound_line[pre_point_loc[1]:] = pre_point_loc[0]

    # 如果保留上半部分
    if method == 3:
        for i in range(rows):
            dir_arr[i, bound_line[i]:] = dir_no_data
    else:
        for i in range(rows):
            dir_arr[i, 0:bound_line[i]] = dir_no_data

    # 获取流向栅格文件的文件名，并生成输出栅格的文件名
    dir_tif_name = os.path.basename(dir_tif_fn)
    prefix, suffix = os.path.splitext(dir_tif_name)
    out_name = prefix + "_mask%d" % method + suffix
    out_fn = os.path.join(os.path.dirname(line_shp_fn), out_name)
    raster.array2tif(out_fn, dir_arr, geo_trans, proj, nd_value=dir_no_data, dtype=1)

    return 1


def get_points(line_shp_fn):
    """

    :param line_shp_fn:
    :return:
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.Open(line_shp_fn, 0)
    layer = ds.GetLayer(0)
    feature = layer.GetFeature(0)
    geom = feature.GetGeometryRef()
    points = [geom.GetPoint(i)[0:2] for i in range(0, geom.GetPointCount())]
    ds.Destroy()

    return points


def check_in_envelope(x, y, envelope):
    if envelope[0] < x < envelope[1] and \
            envelope[3] < y < envelope[2]:
        return True
    else:
        return False


def usage():
    """
    打印脚本的输入参数信息
    :return:
    """
    print("help:\n"
          "  -h: help.\n"
          "  -l: line shapefile.\n"
          "  -t: dir GeoTIFF file.\n"
          "  -d: [1,2,3,4].\n"
          "      1 means only part of the GeoTIFF file that above the input line will be"
          "reserved, the rest part will be set nodata;\n"
          "      2 means below part reserved, above part set nodata;\n"
          "      3 means left part reserved, right part set nodata;\n"
          "      4 means right part reserved, left part set nodata.\n")


def main():
    """

    :return:
    """
    try:
        # 读取命令行参数
        options, args = getopt.getopt(sys.argv[1:], "hl:t:d:", [])
        line_shp = None
        dir_tif = None
        mask_dir = 0
        for name, value in options:
            if name is "-h":
                usage()
            elif name is "-l":
                line_shp = value
            elif name is "-t":
                dir_tif = value
            elif name is "-d":
                mask_dir = value
            else:
                pass

        # 检查参数的正确性
        if not os.path.isfile(line_shp):
            raise IOError("input line .shp file %s does not exist!" % line_shp)
        if not os.path.isfile(dir_tif):
            raise IOError("input dir .tif file %s does not exist!" % dir_tif)
        if mask_dir not in ["1","2","3","4"]:
            raise ValueError("value of the option '-d' must be one of [1,2,3,4]!")

        # 具体的业务函数
        if mask_dir is "1":
            mask_above_or_below(line_shp, dir_tif, 1)
        elif mask_dir is "2":
            mask_above_or_below(line_shp, dir_tif, 2)
        elif mask_dir is "3":
            mask_left_or_right(line_shp, dir_tif, 3)
        else:
            mask_left_or_right(line_shp, dir_tif, 4)

    # 捕捉命令行参数错误
    except getopt.GetoptError:
        usage()
        exit(-1)


if __name__ == "__main__":

    main()

