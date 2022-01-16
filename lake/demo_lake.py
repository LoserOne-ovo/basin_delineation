import os
import sys
import time
import numpy as np
from db_op import get_filter_lake_info, initialize_alter_db, create_lake_table, insert_many_lake_id
from lake_slope import main_lake_per_task



# 构建每个层级湖泊最小面积的字典
lake_thre_dict = {
    1: 100000.0,
    2: 10000.0,
    3: 3000.0,
    4: 1000.0,
    5: 300.0,
    6: 100.0,
    7: 100.0,
    8: 30.0,
    9: 30.0,
    10: 10.0,
    11: 10.0,
    12: 3.0,
    13: 1.0
}


# 构建每个层级河网阈值的字典
river_thre_dict = {
    1: 300000.0,
    2: 100000.0,
    3: 30000.0,
    4: 10000.0,
    5: 3000.0,
    6: 1000.0,
    7: 500.0,
    8: 250.0,
    9: 100.0,
    10: 50.0,
    11: 25.0,
    12: 10.0,
    13: 5.0
}


def filter_lake(level, lake_db, alter_db):
    """
    根据当前层级的湖泊阈值，筛选出湖泊，并将在要同一个流域内处理的湖泊，
    以 流域-湖泊列表 形式， 返回一个字典
    :param level:
    :param lake_db:
    :return:
    """

    # 湖泊面积阈值
    lake_area_ths = lake_thre_dict[level]
    # 查询到的符合条件的湖泊
    lake_list, lake_num = get_filter_lake_info(lake_db, lake_area_ths)

    # 计算每个湖泊暂定的处理层级和对应的流域编号
    process_level = np.zeros((lake_num,), dtype=np.int8)
    loc_basin_code = []

    for eid, lake_info in enumerate(lake_list):
        loc_level = lake_info[2]
        # 如果在当前层级，湖泊被某一个流域完整包含
        if level <= loc_level:
            process_level[eid] = level
            loc_basin_code.append(str(lake_info[level + 2]))
        # 如果在当前层级，湖泊不被某一个流域完整包含
        else:
            process_level[eid] = loc_level
            loc_basin_code.append(str(lake_info[loc_level + 2]))

    loc_basin_code = np.array(loc_basin_code, dtype=str)

    # 按照层级有高到低的顺序，对湖泊进行排序
    sort_idxs = np.argsort(process_level)
    process_level = process_level[sort_idxs]
    loc_basin_code = loc_basin_code[sort_idxs]
    unique_level = np.unique(process_level)

    # 建立流域-湖泊字典字典
    basin_lake_dict = {}
    for i in range(lake_num):
        flag = False
        lake_id = lake_list[sort_idxs[i]][0]
        loc_level = process_level[i]
        loc_basin = loc_basin_code[i]
        for j in unique_level:
            if j > loc_level:
                break
            else:
                top_code = loc_basin[:j]
                if top_code in basin_lake_dict.keys():
                    basin_lake_dict[top_code].append(lake_id)
                    flag = True
                    break

        if flag is False:
            basin_lake_dict[loc_basin] = [lake_id]


    lake_table = "lake_level_%d" % level
    create_lake_table(alter_db, lake_table)
    ins_sql = "INSERT INTO %s VALUES (?)" % lake_table
    ins_val = [(code, ) for code in basin_lake_dict.keys()]
    insert_many_lake_id(alter_db, ins_sql, ins_val)

    return basin_lake_dict


def main_lake(level, lake_db, lake_folder, basin_root, basin_stat_db, alter_db, out_folder):

    bl_dict = filter_lake(level, lake_db, alter_db)
    river_ths = river_thre_dict[level]

    table_name = "level_%d" % level
    basin_table_name = "basin_level_%d" % level
    initialize_alter_db(alter_db, basin_stat_db, table_name, basin_table_name)
    update_sql = "UPDATE %s SET status=? where code=?" % basin_table_name

    if len(bl_dict) == 0:
        print("There is no lake with area larger than the threshold %.1f of level %d!")
    
    else:
        for key, value in bl_dict.items():
            print(key, " -- ", value)
            main_lake_per_task(key, value, river_ths, level, lake_folder, basin_root, 
                               alter_db, update_sql, basin_stat_db, out_folder)


if __name__ == "__main__":


    basin_project_root = r"E:\qyf\data\Australia_multiprocess_test"
    basin_project_db = r"E:\qyf\data\Australia_multiprocess_test\statistic.db"

    lake_shp_folder = r"E:\qyf\data\Australia_multiprocess_test\lake\single_lake"
    lake_db = r"E:\qyf\data\Australia_multiprocess_test\lake\lake_location.db"
    alter_db = r"E:\qyf\data\Australia_multiprocess_test\lake\alter.db"

    out_folder = r"E:\qyf\data\Australia_multiprocess_test\lake\alter_basin"
    
    max_level = 10
    p_level = int(sys.argv[1])
    
    if p_level < 4 or p_level > max_level:
        print("level must be between 4 and %d" % max_level)
        exit(-1)
    
    out_shp_folder = os.path.join(out_folder, "level_%2d" % p_level)
    if not os.path.exists(out_shp_folder):
        os.mkdir(out_shp_folder)
    
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    time_start = time.time()
    main_lake(p_level, lake_db, lake_shp_folder, basin_project_root, basin_project_db, alter_db, out_shp_folder)
    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))






