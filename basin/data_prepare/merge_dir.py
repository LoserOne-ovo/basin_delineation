import os
import sys
sys.path.append(r"../../")
import numpy as np
from util import raster


s_shape = (6000, 6000)


def get_dir_fn(lat, lon):
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

    return str_lat + str_lon + "_dir.tif"


def merge_dir(lon_t, lat_t, dir_root, out_path):

    min_lat, max_lat = lat_t
    min_lon, max_lon = lon_t

    w_shape = (int((max_lat - min_lat) * s_shape[0] / 5), int((max_lon - min_lon) * s_shape[1] / 5))
    merge_dir_arr = np.zeros(w_shape, dtype=np.uint8)
    bench_flag = False
    bench_geotrans = None
    bench_proj = None

    os.chdir(dir_root)
    for i in range(max_lat - 5, min_lat - 5, -5):
        for j in range(min_lon, max_lon, 5):

            dir_fn = get_dir_fn(i, j)
            if os.path.isfile(dir_fn):
                # 读取tif文件
                dir_arr, geo_trans, proj = raster.read_single_tif(dir_fn)
                # 计算输出栅格的地理参考和投影
                if bench_flag is False:
                    ul_lon, width, lon_r, ul_lat, lat_r, height = geo_trans
                    bench_ul_lon = ul_lon - (((j - min_lon) / 5) * s_shape[1]) * width
                    bench_ul_lat = ul_lat - (((max_lat - i - 5) / 5) * s_shape[0]) * height
                    bench_geotrans = (bench_ul_lon, width, lon_r, bench_ul_lat, lat_r, height)
                    bench_proj = proj
                    bench_flag = True
            else:
                dir_arr = np.full(shape=s_shape, fill_value=raster.dir_nodata, dtype=np.uint8)

            # 计算当前栅格在矩阵中的位置
            ul_ridx = int((max_lat - 5 - i) / 5) * s_shape[0]
            ul_cidx = int((j - min_lon) / 5) * s_shape[1]

            merge_dir_arr[ul_ridx:(ul_ridx + s_shape[0]), ul_cidx:(ul_cidx + s_shape[1])] = dir_arr

    # 四条边设置为nodata
    merge_dir_arr[0, :] = raster.dir_nodata
    merge_dir_arr[-1, :] = raster.dir_nodata
    merge_dir_arr[:, 0] = raster.dir_nodata
    merge_dir_arr[:, -1] = raster.dir_nodata

    raster.array2tif(out_path, merge_dir_arr, bench_geotrans, bench_proj, nd_value=raster.dir_nodata, dtype=1)


if __name__ == '__main__':

    dir_folder = r"E:\qyf\data\Asia\dir_mask_tiles"
    out_tif_fn = r"E:\qyf\data\Asia\merge\Asia_mask_dir_merge.tif"
    lon_range = (55, 155)
    lat_range = (0, 60)

    merge_dir(lon_range, lat_range, dir_folder, out_tif_fn)









