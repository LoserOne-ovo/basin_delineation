from multiprocessing import Pool, Lock
from file_op import copy_indivisible_basin, copy_not_divided_basin
from db_op import create_stat_table, get_divisible_basins, get_indivisible_basins, insert_basin_stat_many
from divide_basin import divide_basin_1or2, divide_basin_3, divide_basin_4, divide_basin_5
import os
import time
import traceback


max_process_num = 8


def process_scene_1(record, root, threshold, stat_db_path, sql_statement, log_folder):
    """

    :param record:
    :param root:
    :param threshold:
    :param stat_db_path:
    :param sql_statement:
    :return:
    """
    
    try:
        # 解析流域属性
        code, basin_type, total_area, divide_area, sink_num, island_num = record
        print(code)

        # 拼接工作目录路径
        work_folder = root
        for c in code:
            work_folder = os.path.join(work_folder, c)

        if basin_type == 1 or basin_type == 2:
            result = divide_basin_1or2(work_folder, code, basin_type, sink_num, threshold, stat_db_path, sql_statement)
        elif basin_type == 3:
            result = divide_basin_3(work_folder, code, basin_type, sink_num, threshold, stat_db_path, sql_statement)
        elif basin_type == 4:
            result = divide_basin_4(work_folder, code, sink_num, island_num, threshold, stat_db_path, sql_statement)
        elif basin_type == 5:
            result = divide_basin_5(work_folder, code, sink_num, island_num, threshold, stat_db_path, sql_statement)
        else:
            raise ValueError("Unknown basin type %d " % basin_type)
    
        insert_basin_stat_many(stat_db_path, sql_statement, result)

    except:
        print("Error in basin %s, process_type 1" % code)
        failure_txt = os.path.join(log_folder, "1_" + code + ".txt")
        with open(failure_txt, "w") as fs:
            fs.writelines(traceback.format_exc())
        fs.close()
        

def process_scene_2(code, root, log_folder):
    """
    适用于当前层级不进行划分的流域。
    复制矢量文件，复制栅格文件，并在汇总数据库中插入结果。
    :param record: 数据库查询结果元组（一条记录）
    :param root: 项目（一个大洲为一个项目）的最顶层路径
    :param db_path: 汇总数据库路径
    :param sql_statement: sql语句
    :return:
    """
    try:
        print(code)
        # 复制矢量文件到下一层级目录
        copy_not_divided_basin(root, code)

  
    except:
        print("Error in basin %s, process_type 2" % code)
        failure_txt = os.path.join(log_folder, "2_" + code + ".txt")
        with open(failure_txt, "w") as fs:
            fs.writelines(traceback.format_exc())
        fs.close()

def process_scene_3(code, root, log_folder):
    """
    适用于已经提前预知不适合继续划分的流域。
    复制矢量文件，并在汇总数据库中插入结果。
    :param record: 数据库查询结果元组（一条记录）
    :param root: 项目（一个大洲为一个项目）的最顶层路径
    :param db_path: 汇总数据库路径
    :param sql_statement: sql语句
    :return:
    """
    try:
        print(code)
        # 复制矢量文件到下一层级目录
        copy_not_divided_basin(root, code)
    except:
        print("Error in basin %s, process_type 3" % code)
        failure_txt = os.path.join(log_folder, "3_" + code + ".txt")
        with open(failure_txt, "w") as fs:
            fs.writelines(traceback.format_exc())
        fs.close()


def map_record_not_divided(record):

    code, basin_type, total_area, divide_area, sink_num, island_num = record
    return (code + '0', basin_type, total_area, divide_area, sink_num, island_num, 1)


def map_record_indivisible(record):
    
    code, basin_type, total_area, divide_area, sink_num, island_num = record
    return (code + '0', basin_type, total_area, divide_area, sink_num, island_num, 0)


def main_wd(root, stat_db_path, level, threshold):

    src_table = "level_" + str(level)
    dst_table = "level_" + str(level + 1)

    # 创建下一层级的流域汇总表
    create_stat_table(stat_db_path, dst_table)
    # 插入语句通用模板
    stat_db_insert_sql = "INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?)" % dst_table
    # 多进程错误日志文件
    error_log_folder = os.path.join(root, "log", "level_%02d" % level)
    if not os.path.exists(error_log_folder):
        os.mkdir(error_log_folder)
    
    # basin_list, divide_num, level_divisible_num = get_divisible_basins(stat_db_path, src_table)
    # for i in range(divide_num):
        # process_scene_1(basin_list[i], root, threshold, stat_db_path, stat_db_insert_sql, error_log_folder)
    # for i in range(divide_num, level_divisible_num):
        # process_scene_2(basin_list[i], root, stat_db_path, stat_db_insert_sql, error_log_folder)

    # basin_list = get_indivisible_basins(stat_db_path, src_table)
    # for rec in basin_list:
        # process_scene_3(rec, root, stat_db_path, stat_db_insert_sql, error_log_folder)

    
    #############################
    #   当前层级需要进行划分的流域   #
    #############################
    # 计算当前层级哪些流域需要进行划分
    basin_list, divide_num, level_divisible_num = get_divisible_basins(stat_db_path, src_table)
    print("divided")
    # 进程池
    p_pool = Pool(max_process_num)
    for i in range(divide_num):
        p_pool.apply_async(process_scene_1, args=(basin_list[i], root, threshold, stat_db_path, stat_db_insert_sql, error_log_folder))
    p_pool.close()
    p_pool.join()
    
    ############################
    #   当前层级不需要划分的流域   #
    ############################
    print("not divided")
    # 进程池
    p_pool = Pool(max_process_num)
    for i in range(divide_num, level_divisible_num):
        p_pool.apply_async(process_scene_2, args=(basin_list[i][0], root, error_log_folder))
    p_pool.close()
    p_pool.join()

    ins_val_list = [map_record_not_divided(basin_list[i]) for i in range(divide_num, level_divisible_num)]
    if len(ins_val_list) > 0:
        insert_basin_stat_many(stat_db_path, stat_db_insert_sql, ins_val_list)

    #############################
    #   提前预知的不需要划分的流域   #
    #############################
        print("indivisible")
    basin_list = get_indivisible_basins(stat_db_path, src_table)
    # 进程池
    p_pool = Pool(max_process_num)
    for rec in basin_list:
        p_pool.apply_async(process_scene_3, args=(rec[0], root, error_log_folder))
    p_pool.close()
    p_pool.join()
    
    ins_val_list = [map_record_indivisible(rec) for rec in basin_list]
    if len(ins_val_list) > 0:
        insert_basin_stat_many(stat_db_path, stat_db_insert_sql, ins_val_list)
    
    
if __name__ == "__main__":

    # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    # root_folder = r"E:\qyf\data\Australia"
    # stat_db = r"E:\qyf\data\Australia\statistic.db"
    # top_code = '7'

    # minimum_ths = 10
    # process_level = 5

    # time_start = time.time()
    # main_wd(root_folder, stat_db, process_level, minimum_ths)
    # time_end = time.time()
    # print("total time consumption: %.2f s!" % (time_end - time_start))

    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    root_folder = r"E:\qyf\data\Australia_multiprocess_test"
    stat_db = r"E:\qyf\data\Australia_multiprocess_test\statistic.db"

    minimum_ths = 10
    process_level = 9

    time_start = time.time()
    main_wd(root_folder, stat_db, process_level, minimum_ths)
    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))













