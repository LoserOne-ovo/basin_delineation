import os
import sys
sys.path.append(r"../")
import time
import argparse
import numpy as np
import db_op as dp
import file_op as fp
from util import raster


def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="Gather all sub-basin shp at the same level into a shapefile.")
    parser.add_argument("config", help="configuration file")
    parser.add_argument("level", help="the level of sub-basin shp that you want to gather",
                        type=int, choices=range(1, 13))

    args = parser.parse_args()
    p_root, level_db, min_ths = fp.parse_basin_ini(args.config)
    level = args.level

    return p_root, level_db, min_ths, level


def gather_basin_feature(root, level_db, level):

    # 生成输出目录
    out_folder = os.path.join(root, "basin_result", "raster")
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    basinList = dp.get_level_basins(level_db, level)
    out_fn = os.path.join(out_folder, "level_%d.tif" % level)

    # 创建输出栅格
    bench_dir_tif = os.path.join(root, "raster", "dir.tif")
    rows, cols, geo_trans, proj = raster.get_raster_extent(bench_dir_tif)
    out_arr = np.zeros((rows, cols), dtype=np.float64)
    # 将每一个流域所有的geometry合并成一个Multipolygon
    # 注意，合并后的MultiPolygon可能会自交，所以无法用于地理处理
    for info in basinList:
        src_code, code = info[0:2]
        str_src_code = str(src_code)
        sub_folder = os.path.join(root, *str_src_code)
        mask_tif_path = os.path.join(sub_folder, str_src_code + ".tif")
        mask_db_path = os.path.join(sub_folder, str_src_code + ".db")

        ul_ridx, ul_cidx, sub_rows, sub_cols = dp.get_ul_offset(mask_db_path)
        mask_arr, sub_trans, _ = raster.read_single_tif(mask_tif_path)

        sub_arr = out_arr[ul_ridx:ul_ridx + sub_rows, ul_cidx:ul_cidx + sub_cols]
        sub_arr[mask_arr == 1] = float(code)

    tif_co = ["COMPRESS=DEFLATE", "NUM_THREADS=8", "BIGTIFF=IF_SAFER", "TILED=YES"]
    raster.array2tif(out_fn, out_arr, geo_trans, proj, nd_value=0.0, dtype=raster.OType.F64, opt=tif_co)


    return 1


def main():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    time_start = time.time()

    # 解析参数
    project_root, level_database, minimum_river_threshold, process_level = create_args()
    # 业务函数
    gather_basin_feature(project_root, level_database, process_level)

    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))


if __name__ == "__main__":
    main()
