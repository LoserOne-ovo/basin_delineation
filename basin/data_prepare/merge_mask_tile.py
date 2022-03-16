import os.path
import sys
sys.path.append(r"../../")
import numpy as np
from util import raster


s_shape = (6000, 6000)


def get_tile_prefix(lat, lon):
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

    return str_lat + str_lon


def merge_tile(lon_t, lat_t, mask_tile_folder, src_tile_folder, merge_fn, src_type):


    # 初始化辅助变量
    min_lat, max_lat = lat_t
    min_lon, max_lon = lon_t
    offset_i = 0
    offset_j = 0
    w_shape = (int((max_lat - min_lat) * s_shape[0] / 5), int((max_lon - min_lon) * s_shape[1] / 5))
    bench_flag = False
    bench_geotrans = None
    bench_proj = None

    # 选择要拼接哪一种数据
    if src_type == 1:
        suffix_fn = "_dir.tif"
        src_nodata = 247
        src_dtype = np.uint8
        out_dtype = raster.OType.Byte
    elif src_type == 2:
        suffix_fn = "_upa.tif"
        src_nodata = -9999
        src_dtype = np.float32
        out_dtype = raster.OType.F32
    elif src_type == 3:
        suffix_fn = "_elv.tif"
        src_nodata = -9999
        src_dtype = np.float32
        out_dtype = raster.OType.F32
    else:
        raise RuntimeError("src type should be one of [1, 2, 3]!")

    merge_arr = np.zeros(w_shape, dtype=src_dtype)
    for i in range(max_lat - 5, min_lat - 5, -5):
        offset_j = 0
        for j in range(min_lon, max_lon, 5):
            # 当前范围是否有数据
            prefix = get_tile_prefix(i, j)
            mask_tile_fn = os.path.join(mask_tile_folder, prefix + "_mask.tif")
            if os.path.isfile(mask_tile_fn):
                src_tile_fn = os.path.join(src_tile_folder, prefix + suffix_fn)
                if not os.path.isfile(src_tile_fn):
                    raise IOError("Missing src tile %s!" % src_tile_fn)
                mask_arr, geo_trans, proj = raster.read_single_tif(mask_tile_fn)
                if bench_flag is False:
                    ul_lon, width, lon_r, ul_lat, lat_r, height = geo_trans
                    bench_ul_lon = ul_lon - (((j - min_lon) / 5) * s_shape[1]) * width
                    bench_ul_lat = ul_lat - (((max_lat - i - 5) / 5) * s_shape[0]) * height
                    bench_geotrans = (bench_ul_lon, width, lon_r, bench_ul_lat, lat_r, height)
                    bench_proj = proj
                    bench_flag = True
                src_arr, _, _ = raster.read_single_tif(src_tile_fn)
                src_arr[mask_arr == 0] = src_nodata
                merge_arr[offset_i:offset_i+s_shape[0], offset_j:offset_j+s_shape[1]] = src_arr
            else:
                src_arr = np.full(shape=s_shape, fill_value=src_nodata, dtype=src_dtype)
                merge_arr[offset_i:offset_i + s_shape[0], offset_j:offset_j + s_shape[1]] = src_arr
            offset_j += s_shape[1]
        offset_i += s_shape[0]

    raster.array2tif(merge_fn, merge_arr, bench_geotrans, bench_proj, nd_value=src_nodata, dtype=out_dtype)


if __name__ == "__main__":


    lon_range = (55, 155)
    lat_range = (0, 60)
    mask_folder = r"E:\qyf\data\Asia\mask_tiles"

    # dir
    # src_dir_folder = r"E:\qyf\data\Asia\src\dir"
    # out_dir_fn = r"E:\qyf\data\Asia\merge\Asia_dir.tif"
    # merge_tile(lon_range, lat_range, mask_folder, src_dir_folder, out_dir_fn, 1)
    
    # upa
    # src_upa_folder = r"E:\qyf\data\Asia\src\upa"
    # out_upa_fn = r"E:\qyf\data\Asia\merge\Asia_upa.tif"
    # merge_tile(lon_range, lat_range, mask_folder, src_upa_folder, out_upa_fn, 2)

    # elv
    src_elv_folder = r"E:\qyf\data\Asia\src\elv"
    out_elv_fn = r"E:\qyf\data\Asia\merge\Asia_elv.tif"
    merge_tile(lon_range, lat_range, mask_folder, src_elv_folder, out_elv_fn, 3)





