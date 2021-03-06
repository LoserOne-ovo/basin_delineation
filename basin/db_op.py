import sqlite3
import math


bp_table_name = 'basin_property'
gt_table_name = 'geo_transform'
mo_table_name = 'main_outlets'
sb_table_name = 'sink_bottoms'
is_table_name = 'islands'


bp_sql = "INSERT INTO basin_property VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
mo_sql = "INSERT INTO main_outlets VALUES(?, ?, ?)"
sb_sql = "INSERT INTO sink_bottoms VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
is_sql = "INSERT INTO islands VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
gt_sql = "INSERT INTO geo_transform VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"


######################################
#               创建表               #
######################################


def create_bp_table(db_conn):
    """

    :param db_conn:
    :return:
    """

    db_cursor = db_conn.cursor()
    # 在数据库中建立流域属性的表
    db_cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='%s';" % bp_table_name)
    exist_flag = db_cursor.fetchone()[0]
    # 如果表格已经存在，删除表格
    if exist_flag > 0:
        db_cursor.execute("DROP TABLE %s;" % bp_table_name)

    sql_line = '''CREATE TABLE %s
        (type INTEGER,
        area REAL,
        total_area REAL,
        outlet_lon REAL,
        outlet_lat REAL,
        outlet_ridx INTEGER,
        outlet_cidx INTEGER,
        sink_num INTEGER,
        island_num INTEGER);''' % bp_table_name
    db_cursor.execute(sql_line)
    db_conn.commit()


def create_gt_table(db_conn):
    """

    :param db_conn:
    :return:
    """

    db_cursor = db_conn.cursor()
    db_cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name= '%s';" % gt_table_name)
    exist_flag = db_cursor.fetchone()[0]
    # 如果表格已经存在，删除表格
    if exist_flag > 0:
        db_cursor.execute("DROP TABLE %s;" % gt_table_name)

    sql_line = '''CREATE TABLE %s
        (lon REAL,
        width REAL,
        lon_rotate REAL,
        lat REAL,
        lat_rotate REAL,
        height REAL,
        rows INTEGER,
        cols INTEGER,
        ul_con_ridx INTEGER,
        ul_con_cidx INTEGER);''' % gt_table_name
    db_cursor.execute(sql_line)
    db_conn.commit()


def create_mo_table(db_conn):
    """

    :param db_conn:
    :return:
    """

    db_cursor = db_conn.cursor()
    db_cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name= '%s';" % mo_table_name)
    exist_flag = db_cursor.fetchone()[0]
    # 如果表格已经存在，删除表格
    if exist_flag > 0:
        db_cursor.execute("DROP TABLE %s;" % mo_table_name)

    sql_line = '''CREATE TABLE %s
        (ridx INTEGER NOT NULL,
        cidx INTEGER NOT NULL,
        area REAL NOT NULL);''' % mo_table_name
    db_cursor.execute(sql_line)
    db_conn.commit()


def create_sb_table(db_conn):
    """

    :param db_conn:
    :return:
    """

    db_cursor = db_conn.cursor()
    db_cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name= '%s';" % sb_table_name)
    exist_flag = db_cursor.fetchone()[0]
    if exist_flag > 0:
        db_cursor.execute("DROP TABLE %s;" % sb_table_name)

    sql_line = '''CREATE TABLE %s
        (fid INTEGER,
        ridx INTEGER,
        cidx INTEGER,
        lon REAL,
        lat REAL,
        area REAL,
        is_ridx INTEGER,
        is_cidx INTEGER,
        type INTEGER);''' % sb_table_name
    db_cursor.execute(sql_line)
    db_conn.commit()


def create_is_table(db_conn):
    """

    :param db_conn:
    :return:
    """

    db_cursor = db_conn.cursor()
    db_cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name= '%s';" % is_table_name)
    exist_flag = db_cursor.fetchone()[0]
    # 如果表格已经存在，删除表格
    if exist_flag > 0:
        db_cursor.execute("DROP TABLE %s;" % is_table_name)

    sql_line = '''CREATE TABLE %s
        (fid INTEGER,
        center_ridx REAL,
        center_cidx REAL,
        sample_ridx INTEGER,
        sample_cidx INTEGER,
        radius REAL,
        area REAL,
        ref_cell_area REAL,
        min_ridx INTEGER,
        min_cidx INTEGER,
        max_ridx INTEGER,
        max_cidx INTEGER,
        distance REAL,
        dst_ridx INTEGER,
        dst_cidx INTEGER,
        type INTEGER);''' % is_table_name
    db_cursor.execute(sql_line)
    db_conn.commit()


def create_level_table(db_path, level):

    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name= '%s';" % table_name)
    exist_flag = cursor.fetchone()[0]
    # 如果表格已经存在，删除表格
    if exist_flag > 0:
        cursor.execute("DROP TABLE %s;" % table_name)

    sql_line = '''CREATE TABLE %s
        (code VARCHAR(15),
        type INTEGER,
        total_area REAL,
        divide_area REAL,
        sink_num INTEGER,
        island_num INTEGER,
        divisible INTEGER);''' % table_name
    cursor.execute(sql_line)
    conn.commit()
    conn.close()


######################################
#             数据查询                #
######################################


def get_basin_type(dbpath):

    conn = sqlite3.connect(dbpath)
    cursor = conn.cursor()
    cursor.execute("select TYPE from %s;" % bp_table_name)
    res = cursor.fetchone()
    
    if res is None:
        raise Exception("table basin_property of database %s does not have attribute 'type'!" % dbpath)

    basin_type = res[0]
    if basin_type < 1 or basin_type > 5:
        raise Exception("Unknown basin type in table basin_property of database %s!" % dbpath)

    return basin_type


def get_ul_offset(db_path):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select ul_con_ridx, ul_con_cidx from %s limit 1;" % gt_table_name)
    result = cursor.fetchone()
    conn.close()

    return result


def get_divisible_basins(db_path, level):
    """

    :param db_path:
    :param level:
    :return:
    """
    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select count(*), sum(divide_area) from %s where divisible = 1;" % table_name)
    cur_num, cur_total_area = cursor.fetchone()

    sub_mean_area = cur_total_area / (3 * cur_num)
    divide_num = math.ceil(math.ceil(cur_total_area / sub_mean_area - cur_num) / 8)

    cursor.execute("select code, type, total_area, divide_area, sink_num, island_num from %s "
                   "where divisible = 1 order by divide_area desc;" % table_name)
    basin_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return basin_list, divide_num, cur_num


def get_indivisible_basins(db_path, level):
    """

    :param db_path:
    :param level:
    :return:
    """
    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select code, type, total_area, divide_area, sink_num, island_num from %s "
                   "where divisible = 0;" % table_name)
    basin_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return basin_list


def get_level_basins(db_path, level):
    """

    :param db_path:
    :param level:
    :return:
    """
    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select code from %s;" % table_name)
    basin_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return basin_list


def get_outlet_1(db_path, sink_num):

    # 建立数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 读取流域属性数据
    cursor.execute("select outlet_ridx, outlet_cidx, area from %s;" % bp_table_name)
    outlet_ridx, outlet_cidx, area = cursor.fetchone()

    if sink_num > 0:
        cursor.execute("select * from %s order by area desc;" % sb_table_name)
        sinks = cursor.fetchall()
    else:
        sinks = []
    conn.close()

    return (outlet_ridx, outlet_cidx), area, sinks


def get_outlet_4(db_path, all_sink_num, all_island_num):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 先查询四个主要外流区
    cursor.execute("select * from %s order by area desc;" % mo_table_name)
    outlets = cursor.fetchall()
    outlets_num = len(outlets)

    # 查询大陆内流区和岛屿内流区
    if all_sink_num > 0:
        cursor.execute("select * from %s where type = 1 order by area desc;" % sb_table_name)
        sinks = cursor.fetchall()
        sink_num = len(sinks)
        i_sink_num = all_sink_num - sink_num
        if i_sink_num > 0:
            cursor.execute("select * from %s where type = 2 order by area desc;" % sb_table_name)
            i_sinks = cursor.fetchall()
        else:
            i_sinks = None
    else:
        sink_num = i_sink_num = 0
        sinks = i_sinks = []

    # 查询归属于大陆的岛屿和其他岛屿
    if all_island_num > 0:
        cursor.execute("select * from %s where type = 1 order by area desc;" % is_table_name)
        m_islands = cursor.fetchall()
        m_island_num = len(m_islands)
        island_num = all_island_num - m_island_num
        if island_num > 0:
            cursor.execute("select * from %s where type = 2 order by area desc;" % is_table_name)
            islands = cursor.fetchall()
        else:
            islands = []
    else:
        m_island_num = island_num = 0
        m_islands = islands = []

    return outlets, outlets_num, sinks, sink_num, islands, island_num, m_islands, m_island_num, i_sinks, i_sink_num


def get_outlet_5(db_path, sink_num):


    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询所有岛屿
    cursor.execute("select * from %s where type=2 order by area desc;" % is_table_name)
    islands = cursor.fetchall()

    # 查询所有内流区
    if sink_num > 0:
        cursor.execute("select * from %s where type=2 order by area desc;" % sb_table_name)
        sinks = cursor.fetchall()
    else:
        sinks = []

    # 查询总面积
    cursor.execute("select total_area from %s;" % bp_table_name)
    total_area = cursor.fetchone()[0]

    return total_area, islands, sinks


######################################
#             数据插入                #
######################################


def insert_basin_stat(db_path, level, ins_value):
    """

    :param db_path:
    :param level:
    :param ins_value:
    :return:
    """
    table_name = "level_%d" % level
    sql_line = "INSERT INTO %s VALUES(?,?,?,?,?,?,?);" % table_name
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    cursor.execute(sql_line, ins_value)
    conn.commit()
    conn.close()


def insert_basin_stat_many(db_path, level, ins_value_list):
    """

    :param db_path:
    :param level:
    :param ins_value_list:
    :return:
    """
    table_name = "level_%d" % level
    sql_line = "INSERT INTO %s VALUES(?,?,?,?,?,?,?);" % table_name
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.executemany(sql_line, ins_value_list)
    conn.commit()
    conn.close()











