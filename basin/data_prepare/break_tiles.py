import os
import sys
sys.path.append(r"../../")
import numpy as np
from util import raster


s_shape = (6000, 6000)
mask_nodata = 0


def get_mask_fn(lat, lon):
    # 经度
    if lat < 0:
        str_lat = 's' + '{:0>2d}'.format(abs(lat))
    else:
        str_lat = 'n' + '{:0>2d}'.format(lat)
    # 纬度
    if lon < 0:
        str_lon = 'w' + '{:0>3d}'.format(abs(lon))
    else:
        str_lon = 'e' + '{:0>3d}'.format(lon)

    return str_lat + str_lon + "_mask.tif"


def break_mask_into_tiles(lon_t, lat_t, mask_tif, out_put_folder):
    """

    :param lon_t:
    :param lat_t:
    :param mask_tif:
    :param out_put_folder:
    :return:
    """

    if not os.path.isdir(out_put_folder):
        raise RuntimeError("Directory %s does not exist!" % out_put_folder)

    # 读取栅格数据
    mask_arr, geo_trans, proj = raster.read_single_tif(mask_tif)
    rows, cols = mask_arr.shape
    lon, width, lon_r, lat, lat_r, height = geo_trans

    # 初始化辅助变量
    min_lat, max_lat = lat_t
    min_lon, max_lon = lon_t
    offset_i = 0
    offset_j = 0

    # 检查掩膜栅格是否是由整数幅栅格影响拼接而成
    if (rows % s_shape[0]) != 0 or (cols % s_shape[1]) != 0:
        raise RuntimeError("Input mask tif is invalid!")

    for i in range(max_lat - 5, min_lat - 5, -5):
        offset_j = 0
        for j in range(min_lon, max_lon, 5):
            tile_arr = mask_arr[offset_i:offset_i+s_shape[0], offset_j:offset_j+s_shape[1]].copy()
            # 只有该块栅格有数据时，才生成相应的掩膜文件
            if np.sum(tile_arr != 0) > 0:
                out_path = os.path.join(out_put_folder, get_mask_fn(i, j))
                tile_lon = lon + offset_j * width
                tile_lat = lat + offset_i * height
                tile_geotrans = (tile_lon, width, lon_r, tile_lat, lat_r, height)
                raster.array2tif(out_path, tile_arr, tile_geotrans, proj, nd_value=mask_nodata, dtype=raster.OType.Byte)
            offset_j += s_shape[1]
        offset_i += s_shape[0]


if __name__ == "__main__":

    lon_range = (55, 155)
    lat_range = (0, 60)

    input_mask_tif = r"E:\qyf\data\Asia\merge\Asia_dir_track.tif"
    tile_tif_out_folder = r"E:\qyf\data\Asia\mask_tiles"
    break_mask_into_tiles(lon_range, lat_range, input_mask_tif, tile_tif_out_folder)