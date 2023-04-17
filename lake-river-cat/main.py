import time
import argparse
import file_op as fp
from divide_lake_basin import workflow


def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="divide basins of a given level into sub basins via lake")
    parser.add_argument("config", help="configuration file")
    parser.add_argument("level", help="level basin to be divided", type=int, choices=range(1, 13))
    parser.add_argument("-p", "--process", help="max processor num of computer", default=1, type=int)
    args = parser.parse_args()

    level = args.level
    max_p_num = args.process
    p_root, basin_db, alter_db, lake_shp, min_ths, code, src_code = fp.parse_lake_ini(args.config)

    return src_code, code, level, p_root, lake_shp, basin_db, alter_db, min_ths, max_p_num


def main():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    time_start = time.time()

    # 解析参数
    src_code, code, level, root, lake_shp, basin_db, alter_db, min_r_ths, p_num = create_args()
    # 业务函数
    workflow(basin_db, alter_db, src_code, code, level, root, lake_shp, min_r_ths, p_num)

    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))


if __name__ == "__main__":
    main()
