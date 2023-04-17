import time
import argparse
import db_op as dp
import file_op as fp
import divide_basin as di
from multiprocessing import Pool
from functools import partial


def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="divide basins of a given level into sub basins at next level")
    parser.add_argument("config", help="configuration file")
    parser.add_argument("level", help="level basin to be divided", type=int, choices=range(1, 15))
    parser.add_argument("-p", "--process", help="max processor num of computer", default=1, type=int)
    args = parser.parse_args()

    p_root, level_db, min_ths = fp.parse_basin_ini(args.config)
    level = args.level
    max_p_num = args.process

    return p_root, level_db, min_ths, level, max_p_num


def process_scene_1(record, root, threshold):
    """

    :param record:
    :param root:
    :param threshold:
    :return:
    """
    # 解析流域属性
    basin_type = record[3]
    try:
        if basin_type == 1:
            result = di.divide_basin_1(record, root, threshold)
        elif basin_type == 2:
            result = di.divide_basin_2(record, root, threshold)
        elif basin_type == 3:
            result = di.divide_basin_3(record, root, threshold)
        elif basin_type == 4:
            result = di.divide_basin_4(record, root, threshold)
        elif basin_type == 5:
            result = di.divide_basin_5(record, root, threshold)
        else:
            raise ValueError("Unknown basin type %d " % basin_type)
        return result

    except:
        print("Error in %s - %s" % (record[0], record[1]))
        raise RuntimeError("Interrupt!")


def get_divided_basin_info(src_basin_list, sub_basin_list, basin_num, hwDict):

    for i in range(basin_num):
        down_code = src_basin_list[i][2]
        subInfoList = sub_basin_list[i]

        for probe, subBasinInfo in enumerate(subInfoList):
            if probe == 0 and down_code != 0:
                basin_type = subBasinInfo[3]
                if basin_type == 1 or basin_type == 2:
                    rec = list(subBasinInfo)
                    rec[2] = hwDict[down_code] if down_code != -1 else down_code
                    yield tuple(rec)
                else:
                    yield subBasinInfo
            else:
                yield subBasinInfo


def get_not_divided_basin_info(record, hwDict):

    rec = list(record)
    rec[1] = rec[1] * 10
    if (rec[3] == 1 or rec[3] == 2) and rec[2] > 0:
        rec[2] = hwDict[rec[2]]
    return tuple(rec)


def main_wd(root, level_db, threshold, level, p_num):
    """

    :param root:
    :param level_db:
    :param threshold:
    :param level:
    :param p_num:
    :return:
    """

    # 计算当前层级哪些流域需要进行划分
    basin_list, divide_num, level_divisible_num = dp.get_divisible_basins_by_mae(level_db, level)
    if level_divisible_num <= 0:
        print("There is no basin big enough to divide. Program exit.")
        exit(0)

    # 不可划分的流域
    in_basin_list, indi_num = dp.get_indivisible_basins(level_db, level)
    # 创建下一层级的流域汇总表
    dp.create_level_table(level_db, level + 1)
    # 进程池
    p_pool = Pool(p_num)

    # 计算每个流域划分之后接受上游来水的源头流域
    hwDict = {}
    for i in range(divide_num, level_divisible_num):
        if basin_list[i][3] == 2:
            basin_code = basin_list[i][1]
            hwDict[basin_code] = basin_code * 10
    for i in range(indi_num):
        if in_basin_list[i][3] == 2:
            basin_code = in_basin_list[i][1]
            hwDict[basin_code] = basin_code * 10

    print("divisible: %d" % level_divisible_num)
    print("divide: %d" % divide_num)
    partial_p1 = partial(process_scene_1, root=root, threshold=threshold)
    result = p_pool.map(partial_p1, basin_list[0:divide_num])

    for i in range(divide_num):
        if basin_list[i][3] == 2:
            basin_code = basin_list[i][1]
            hwDict[basin_code] = result[i].pop()

    ins_val_list = get_divided_basin_info(basin_list[0:divide_num], result, divide_num, hwDict)
    dp.insert_basin_stat(level_db, level + 1, ins_val_list)

    # 不需要划分的流域
    print("not divide: %d" % (level_divisible_num - divide_num))
    if level_divisible_num - divide_num > 0:
        ins_val_list = [get_not_divided_basin_info(basin_list[i], hwDict)
                        for i in range(divide_num, level_divisible_num)]
        dp.insert_basin_stat(level_db, level + 1, ins_val_list)

    # 不可划分的流域
    print("indivisible: %d" % indi_num)
    if indi_num > 0:
        ins_val_list = [get_not_divided_basin_info(rec, hwDict) for rec in in_basin_list]
        dp.insert_basin_stat(level_db, level + 1, ins_val_list)

    
if __name__ == "__main__":


    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    time_start = time.time()

    # 解析参数
    project_root, level_database, minimum_river_threshold, process_level, max_process_num = create_args()
    # 业务函数
    main_wd(project_root, level_database, minimum_river_threshold, process_level, max_process_num)

    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))
