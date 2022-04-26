import os
import sys
sys.path.append(r"../")
import time
import argparse
import traceback
import file_op as fp
import db_op as dp
import divide_basin as di
from multiprocessing import Pool


def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="divide basins of a given level into sub basins at next level")
    parser.add_argument("config", help="configuration file")
    parser.add_argument("level", help="level basin to be divided", type=int, choices=range(1, 16))
    parser.add_argument("-p", "--process", help="max processor num of computer", default=1, type=int)
    args = parser.parse_args()

    ini_file = args.config
    if not os.path.isfile(ini_file):
        raise RuntimeError("Configuration file does not exist!")

    # 配置文件中要读取三个参数
    tgt_args = ["project_root", "level_database", "minimum_river_threshold"]
    ini_dict = {}
    with open(ini_file, "r") as fs:
        line = fs.readline()
        while line:
            line_str = line.split("=")
            if line_str[0] in tgt_args:
                ini_dict[line_str[0]] = line_str[1]
            line = fs.readline()
    fs.close()

    flag = True
    # 检查项目根目录参数
    if tgt_args[0] in ini_dict.keys():
        p_root = ini_dict[tgt_args[0]].strip()
        if not os.path.exists(p_root):
            print("The path of %s does not exist!" % tgt_args[0])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[0])
        flag = False
    # 检查汇总数据库参数
    if tgt_args[1] in ini_dict.keys():
        level_db = ini_dict[tgt_args[1]].strip()
        if not os.path.isfile(level_db):
            print("The path of %s does not exist!" % tgt_args[1])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[1])
        flag = False
    # 检查河网阈值
    if tgt_args[2] in ini_dict.keys():
        min_ths = ini_dict[tgt_args[2]].strip()
        if not check_float(min_ths):
            print("%s could not be converted to a float!" % tgt_args[2])
            flag = False
        else:
            min_ths = float(min_ths)
            if min_ths <= 0.:
                print("%s must be larger than 0!" % tgt_args[2])
                flag = False
    else:
        print("%s not found in the config file!" % tgt_args[2])
        flag = False

    if flag is False:
        exit(-1)

    level = args.level
    max_p_num = args.process

    return p_root, level_db, min_ths, level, max_p_num


def check_float(num_str):
    """
    check whether the input string could be converted to a float
    :param num_str:
    :return:
    """
    try:
        float(num_str)
        return True
    except:
        return False


def process_scene_1(record, root, level_db, threshold, level, log_folder):
    """

    :param record:
    :param root:
    :param level_db:
    :param threshold:
    :param level:
    :param log_folder
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
            result = di.divide_basin_1or2(work_folder, code, basin_type, sink_num, threshold)
        elif basin_type == 3:
            result = di.divide_basin_3(work_folder, code, basin_type, sink_num, threshold)
        elif basin_type == 4:
            result = di.divide_basin_4(work_folder, code, sink_num, island_num, threshold)
        elif basin_type == 5:
            result = di.divide_basin_5(work_folder, code, sink_num, island_num, threshold)
        else:
            raise ValueError("Unknown basin type %d " % basin_type)
    
        dp.insert_basin_stat_many(level_db, level + 1, result)

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
    :param code: 数据库查询结果元组（一条记录）
    :param root: 项目（一个大洲为一个项目）的最顶层路径
    :param log_folder: 汇总数据库路径
    :return:
    """
    try:
        print(code)
        # 复制矢量文件到下一层级目录
        fp.copy_not_divided_basin(root, code)

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
    :param code: 数据库查询结果元组（一条记录）
    :param root: 项目（一个大洲为一个项目）的最顶层路径
    :param log_folder: 汇总数据库路径
    :return:
    """
    try:
        print(code)
        # 复制矢量文件到下一层级目录
        fp.copy_not_divided_basin(root, code)

    except:
        print("Error in basin %s, process_type 3" % code)
        failure_txt = os.path.join(log_folder, "3_" + code + ".txt")
        with open(failure_txt, "w") as fs:
            fs.writelines(traceback.format_exc())
        fs.close()


def map_record_not_divided(record):
    """

    :param record:
    :return:
    """
    code, basin_type, total_area, divide_area, sink_num, island_num = record
    return (code + '0', basin_type, total_area, divide_area, sink_num, island_num, 1)


def map_record_indivisible(record):
    """

    :param record:
    :return:
    """
    code, basin_type, total_area, divide_area, sink_num, island_num = record
    return (code + '0', basin_type, total_area, divide_area, sink_num, island_num, 0)


def main_wd(root, level_db, threshold, level, p_num):
    """

    :param root:
    :param level_db:
    :param threshold:
    :param level:
    :param p_num:
    :return:
    """
    # 创建下一层级的流域汇总表
    dp.create_level_table(level_db, level + 1)
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
    basin_list, divide_num, level_divisible_num = dp.get_divisible_basins(level_db, level)
    print("divided")
    # 进程池
    p_pool = Pool(p_num)
    for i in range(divide_num):
        p_pool.apply_async(process_scene_1, args=(basin_list[i], root, level_db, threshold, level, error_log_folder))
    p_pool.close()
    p_pool.join()
    
    ############################
    #   当前层级不需要划分的流域   #
    ############################
    print("not divided")
    # 进程池
    p_pool = Pool(p_num)
    for i in range(divide_num, level_divisible_num):
        p_pool.apply_async(process_scene_2, args=(basin_list[i][0], root, error_log_folder))
    p_pool.close()
    p_pool.join()

    ins_val_list = [map_record_not_divided(basin_list[i]) for i in range(divide_num, level_divisible_num)]
    if len(ins_val_list) > 0:
        dp.insert_basin_stat_many(level_db, level + 1, ins_val_list)

    #############################
    #   提前预知的不需要划分的流域   #
    #############################
    print("indivisible")
    basin_list = dp.get_indivisible_basins(level_db, level)
    # 进程池
    p_pool = Pool(p_num)
    for rec in basin_list:
        p_pool.apply_async(process_scene_3, args=(rec[0], root, error_log_folder))
    p_pool.close()
    p_pool.join()
    
    ins_val_list = [map_record_indivisible(rec) for rec in basin_list]
    if len(ins_val_list) > 0:
        dp.insert_basin_stat_many(level_db, level + 1, ins_val_list)
    
    
if __name__ == "__main__":


    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    time_start = time.time()

    # 解析参数
    project_root, level_database, minimum_river_threshold, process_level, max_process_num = create_args()
    # 业务函数
    main_wd(project_root, level_database, minimum_river_threshold, process_level, max_process_num)

    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))













