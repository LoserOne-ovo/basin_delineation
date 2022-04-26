import sqlite3


# 构建每个层级湖泊最小面积的字典
lake_thre_dict = {
    1: 100000.0,
    2: 10000.0,
    3: 3000.0,
    4: 1000.0,
    5: 300.0,
    6: 100.0,
    7: 30.0,
    8: 10.0,
    9: 3.0,
    10: 3.0,
    11: 1.0,
    12: 1.0,
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
}


location_table = "lake_location"
location_insert_sql = "INSERT INTO lake_location VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
bp_table_name = 'basin_property'
gt_table_name = 'geo_transform'
mo_table_name = 'main_outlets'
sb_table_name = 'sink_bottoms'
is_table_name = 'islands'


def get_lake_ths(level):
    return lake_thre_dict[level]
    

def get_river_ths(level):
    return river_thre_dict[level]


#######################
#    流域属性信息查询    #
#######################
def get_ul_offset(db_path):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select ul_con_ridx, ul_con_cidx from geo_transform;")
    result = cursor.fetchone()
    conn.close()

    return result


def get_sub_basin_info(db_path, top_n_code, level):
    """

    :param db_path:
    :param top_n_code:
    :param level:
    :return:
    """

    # 判断层级顺序是否正确
    top_n_level = len(top_n_code)
    if top_n_level >= level:
        raise RuntimeError("top_n_level is lower than input level!")

    table = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select code from %s where code like '%s';" % (table, top_n_code + "%"))
    result = cursor.fetchall()
    conn.close()

    return result


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


##################
#    预处理阶段    #
##################
def create_loc_table(db_path):
    """
    建立存储湖泊--流域位置信息的sqlite数据库
    :param db_path:
    :return:
    """

    table_name = location_table
    db_conn = sqlite3.connect(db_path)
    db_cursor = db_conn.cursor()
    # 在数据库中建立湖泊对应流域的的表
    db_cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='%s';" % table_name)
    res = db_cursor.fetchone()
    if res[0] == 0:
        pass
    elif res[0] == 1:
        db_cursor.execute("DROP TABLE %s;" % table_name)
    else:
        raise Exception("wrong number of table %s in the database %s" % (table_name, db_path))

    sqline = '''CREATE TABLE %s
        (lake_id INTEGER NOT NULL,
        lake_area REAL NOT NULL,
        contain_lv INTEGER,
        lv_1 CHAR(1),
        lv_2 CHAR(2),
        lv_3 CHAR(3),
        lv_4 CHAR(4),
        lv_5 CHAR(5),
        lv_6 CHAR(6),
        lv_7 CHAR(7),
        lv_8 CHAR(8),
        lv_9 CHAR(9),
        lv_10 CHAR(10),
        lv_11 CHAR(11),
        lv_12 CHAR(12),
        lv_13 CHAR(13),
        lv_14 CHAR(14),
        lv_15 CHAR(15));''' % table_name
    db_cursor.execute(sqline)
    db_conn.commit()
    db_conn.close()


def insert_location_info(db_path, ins_value):
    """

    :param db_path:
    :param ins_value:
    :return:
    """
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.execute(location_insert_sql, ins_value)
    conn.commit()
    conn.close()


###############################
#    挑选面积大于层级阈值的湖泊    #
###############################
def initialize_alter_db(alter_db, level_db, level):
    """
    创建数据库，用于记录哪些流域中有湖泊，进行了湖泊坡面的提取处理。哪些流域没有做湖泊处理。
    :param alter_db:
    :param level_db:
    :param level:
    :return:
    """
    # 查询当前层级所有流域
    table_name = "level_%d" % level
    conn = sqlite3.connect(level_db)
    cursor = conn.cursor()
    cursor.execute("select code from %s;" % table_name)
    basin_ids = cursor.fetchall()
    cursor.close()
    conn.close()

    def map_basin(record):
        return (record[0], 0)

    # 初始化插入列表。先认为所有流域都不含湖泊
    ins_val = [map_basin(rec) for rec in basin_ids]
    create_alter_table(alter_db, level)
    create_lake_alter_table(alter_db, level)
    conn = sqlite3.connect(alter_db)
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO %s VALUES (?, ?)" % table_name, ins_val)
    conn.commit()
    conn.close()


##################################
#    记录哪些流域做了湖泊坡面的处理    #
##################################
def create_alter_table(db_path, level):
    """

    :param db_path:
    :param level:
    :return:
    """
    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='%s';" % table_name)
    res = cursor.fetchone()
    if res[0] == 0:
        pass
    elif res[0] == 1:
        cursor.execute("DROP TABLE %s;" % table_name)
    else:
        raise Exception("wrong number of table %s in the database %s" % (table_name, db_path))

    sqline = '''CREATE TABLE %s
        (code VARCHAR(15),
        status SMALLINT);''' % table_name
    cursor.execute(sqline)
    conn.commit()
    conn.close()


def create_lake_alter_table(db_path, level):
    """
    
    :param db_path:
    :param level:
    :return:
    """
    table_name = "lake_level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS %s;" % table_name)
    
    sqline = '''CREATE TABLE %s
        (code VARCHAR(15),
        lake_id INTEGER);''' % table_name
    cursor.execute(sqline)
    conn.commit()
    conn.close()


def get_filter_lake_info(db_path, area_ths):
    """

    :param db_path:
    :param area_ths:
    :return:
    """
    table_name = location_table
    sql_line = "select * from %s where lake_area > %.4f and contain_lv > 1 order by lake_id;" % (table_name, area_ths)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql_line)
    result = cursor.fetchall()

    return result, len(result)


def update_many_alter_status(db_path, level, update_val):
    """

    :param db_path:
    :param level:
    :param update_val:
    :return:
    """
    table_name = "level_%d" % level
    update_sql = "UPDATE %s SET status=? where code=?" % table_name
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.executemany(update_sql, update_val)
    conn.commit()
    conn.close()


def insert_lale_alter_info(db_path, level, insert_val):
    """

    :param db_path:
    :param level:
    :param update_val:
    :return:
    """
    table_name = "lake_level_%d" % level
    insert_sql = "INSERT INTO %s VALUES(?, ?);" % table_name
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.executemany(insert_sql, insert_val)
    conn.commit()
    conn.close()


###############
#    后处理    #
###############
def get_alter_basin_info(alter_db, level):
    """

    :param alter_db:
    :param level:
    :return:
    """
    table_name = "level_%d" % level
    conn = sqlite3.connect(alter_db)
    cursor = conn.cursor()
    cursor.execute("select * from %s;" % table_name)
    result = cursor.fetchall()
    return result


def get_alter_lake_info(alter_db, level):
    """

    :param alter_db:
    :param level:
    :return:
    """
    table_name = "lake_level_%d" % level
    conn = sqlite3.connect(alter_db)
    cursor = conn.cursor()
    cursor.execute("select * from %s;" % table_name)
    result = cursor.fetchall()
    
    return result







