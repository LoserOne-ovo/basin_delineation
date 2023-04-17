import os


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


def parse_basin_ini(ini_file):

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
    p_root = level_db = min_ths = None
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
        if not os.path.isdir(os.path.dirname(level_db)):
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

    return p_root, level_db, min_ths
