import os
import time
import argparse
import numpy as np
import db_op as dp
import file_op as fp
from multiprocessing import Pool
from lake_slope import main_lake_per_task



def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="mosaic lake and lake slope into basin")
    parser.add_argument("basin_config", help="basin configuration file")
    parser.add_argument("lake_config", help="lake configuration file")
    parser.add_argument("level", help="level basin to burn lake hillslope", type=int, choices=range(1, 16))
    parser.add_argument("-p", "--process", help="max processor num of computer", default=1, type=int)
    args = parser.parse_args()

    basin_ini_file = args.basin_config
    lake_ini_file = args.lake_config

    p_root, level_db, min_ths = fp.parse_basin_ini(basin_ini_file)
    lake_db, alter_db, lake_folder, alter_folder = fp.parse_lake_ini(lake_ini_file)
    
    level = args.level
    max_p_num = args.process
    alter_folder = os.path.join(alter_folder, "level_%02d" % level)
    if not os.path.exists(alter_folder):
        os.mkdir(alter_folder)

    return p_root, level_db, lake_db, alter_db, lake_folder, alter_folder, level, max_p_num


def filter_lake(level, lake_db):
    """
    根据当前层级的湖泊阈值，筛选出湖泊，并将在要同一个流域内处理的湖泊，
    以 流域-湖泊列表 形式， 返回一个字典
    :param level:
    :param lake_db:
    :return:
    """

    # 湖泊面积阈值
    lake_area_ths = dp.get_lake_ths(level + 1)
    # 查询到的符合条件的湖泊，面积大于当前层级设定的阈值
    lake_list, lake_num = dp.get_filter_lake_info(lake_db, lake_area_ths)

    # 计算每个湖泊暂定的处理层级和对应的流域编号
    process_level = np.zeros((lake_num,), dtype=np.int8)
    loc_basin_code = []
    # 对于每一个湖泊
    for eid, lake_info in enumerate(lake_list):
        loc_level = lake_info[2]
        # 如果在当前层级，湖泊被某一个流域完整包含，那么就在当前层级处理
        if level <= loc_level:
            process_level[eid] = level
            loc_basin_code.append(str(lake_info[level + 2]))
        # 如果在当前层级，湖泊不被某一个流域完整包含，那么就在完整包含的层级处理
        else:
            process_level[eid] = loc_level
            loc_basin_code.append(str(lake_info[loc_level + 2]))
            
    loc_basin_code = np.array(loc_basin_code, dtype=str)
    # 按照层级由高到低的顺序，对湖泊所处的流域进行排序
    sort_idxs = np.argsort(process_level)

    process_level = process_level[sort_idxs]
    loc_basin_code = loc_basin_code[sort_idxs]
    unique_level = np.unique(process_level)

    # 建立流域-湖泊字典
    basin_lake_dict = {}
    for i in range(lake_num):
        flag = False
        # 湖泊id
        lake_id = lake_list[sort_idxs[i]][0]
        # 湖泊所处的层级
        loc_level = process_level[i]
        # 湖泊所处的流域
        loc_basin = loc_basin_code[i]
        # 判断湖泊所处流域的上级流域是否已经存在于流域-湖泊字典中
        for j in unique_level:
            if j > loc_level:
                break
            else:
                top_code = loc_basin[:j]
                # 如果上级流域已经在字典中，那么就将当前湖泊放到上级流域中进行处理
                if top_code in basin_lake_dict.keys():
                    basin_lake_dict[top_code].append(lake_id)
                    flag = True
                    break
        # 如果上级流域不在字典中，那么当前湖泊就在其所处的流域中进行处理
        if flag is False:
            basin_lake_dict[loc_basin] = [lake_id]

    return basin_lake_dict


def main_lake(basin_root, level_db, lake_db, alter_db, lake_folder, alter_folder, level, processor_num):
    """

    :param basin_root:
    :param level_db:
    :param lake_db:
    :param alter_db:
    :param lake_folder:
    :param out_folder:
    :param level:
    :param processor_num:
    :return:
    """

    bl_dict = filter_lake(level, lake_db)
    river_ths = dp.get_river_ths(level + 1)
    dp.initialize_alter_db(alter_db, level_db, level)
    log_folder = os.path.join(basin_root, "log", "lake_level_%02d" % level)
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
        
    # for key, value in bl_dict.items():
        # main_lake_per_task(key, value, basin_root, level_db, alter_db, level, river_ths, lake_folder, alter_folder)
    pool = Pool(processor_num)
    for key, value in bl_dict.items():
        pool.apply_async(main_lake_per_task, args=(key, value, basin_root, level_db, alter_db, level, river_ths, lake_folder, alter_folder, log_folder))
    pool.close()
    pool.join()


if __name__ == "__main__":

    time_start = time.time()
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_start)))
    basin_project_root, level_db_path, lake_db_path, alter_db_path, lake_shp_folder, alter_shp_folder, p_level, p_num = create_args()
    main_lake(basin_project_root, level_db_path, lake_db_path, alter_db_path, lake_shp_folder, alter_shp_folder, p_level, p_num)
    time_end = time.time()
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_end)))
    print("total time consumption: %.2f s!" % (time_end - time_start))

