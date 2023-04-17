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


def check_int(num_str):
    """
    check whether the input string could be converted to an integer
    :param num_str:
    :return:
    """
    try:
        int(num_str)
        return True
    except:
        return False


def parse_lake_ini(ini_file):
    """

    :param ini_file:
    :return:
    """
    if not os.path.isfile(ini_file):
        raise RuntimeError("Configuration file does not exist!")

    # 配置文件中要7个参数
    tgt_args = ["project_root", "basin_database", "alter_database", "lake_shp",
                "minimum_river_threshold", "code", "src_code"]
    ini_dict = {}
    with open(ini_file, "r") as fs:
        line = fs.readline()
        while line:
            line_str = line.split("=")
            arg_name = line_str[0].strip()
            if arg_name in tgt_args:
                ini_dict[arg_name] = line_str[1].strip()
            line = fs.readline()
    fs.close()

    flag = True
    p_root = basin_db = alter_db = lake_shp = min_ths = code = src_code = None

    # 检查项目根目录参数
    if tgt_args[0] in ini_dict.keys():
        p_root = ini_dict[tgt_args[0]]
        if not os.path.exists(p_root):
            print("The path of %s does not exist!" % tgt_args[0])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[0])
        flag = False

    # 检查流域数据库参数
    if tgt_args[1] in ini_dict.keys():
        basin_db = ini_dict[tgt_args[1]]
        if not os.path.exists(basin_db):
            print("The path of %s does not exist!" % tgt_args[1])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[1])
        flag = False

    # 检查湖泊数据库参数
    if tgt_args[2] in ini_dict.keys():
        alter_db = ini_dict[tgt_args[2]]
        if not os.path.isdir(os.path.dirname(alter_db)):
            print("The path of %s does not exist!" % tgt_args[2])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[2])
        flag = False

    # 检查湖泊文件参数
    if tgt_args[3] in ini_dict.keys():
        lake_shp = ini_dict[tgt_args[3]]
        if not os.path.exists(lake_shp):
            print("The path of %s does not exist!" % tgt_args[3])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[3])
        flag = False

    # 检查河网阈值
    if tgt_args[4] in ini_dict.keys():
        min_ths = ini_dict[tgt_args[4]]
        if not check_float(min_ths):
            print("%s could not be converted to a float!" % tgt_args[4])
            flag = False
        else:
            min_ths = float(min_ths)
            if min_ths <= 0.:
                print("%s must be larger than 0!" % tgt_args[4])
                flag = False
    else:
        print("%s not found in the config file!" % tgt_args[4])
        flag = False

    # 检查大洲编号
    if tgt_args[5] in ini_dict.keys():
        code = ini_dict[tgt_args[5]]
        if not check_int(code):
            print("%s could not be converted to a float!" % tgt_args[5])
            flag = False
        else:
            code = int(code)
            if code <= 0:
                print("%s must be larger than 0!" % tgt_args[5])
                flag = False
    else:
        print("%s not found in the config file!" % tgt_args[5])
        flag = False

    # 检查大洲编号
    if tgt_args[6] in ini_dict.keys():
        src_code = ini_dict[tgt_args[6]]
        if not check_int(src_code):
            print("%s could not be converted to a float!" % tgt_args[6])
            flag = False
        else:
            src_code = int(src_code)
            if src_code <= 0:
                print("%s must be larger than 0!" % tgt_args[6])
                flag = False
    else:
        print("%s not found in the config file!" % tgt_args[6])
        flag = False

    if flag is False:
        exit(-1)

    return p_root, basin_db, alter_db, lake_shp, min_ths, code, src_code
