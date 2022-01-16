import sqlite3


def create_loc_table(db_path):
    """
    建立存储湖泊--流域位置信息的sqlite数据库
    :param db_path:
    :return:
    """

    table_name = "lake_location"
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


def initialize_alter_db(db_path, stat_db_path, table_name, basin_table_name):

    conn = sqlite3.connect(stat_db_path)
    cursor = conn.cursor()
    cursor.execute("select code from %s;" % table_name)
    basin_ids = cursor.fetchall()
    cursor.close()
    conn.close()

    def map_basin(record):
        return (record[0], 0)

    ins_val = [map_basin(rec) for rec in basin_ids]
    create_alter_table(db_path, basin_table_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO %s VALUES (?, ?)" % basin_table_name, ins_val)
    conn.commit()
    conn.close()


def create_alter_table(db_path, table_name):

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
        status INTEGER);''' % table_name
    cursor.execute(sqline)
    conn.commit()
    conn.close()


def create_lake_table(db_path, table_name):

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
        (code VARCHAR(15));''' % table_name
    cursor.execute(sqline)
    conn.commit()
    conn.close()


def get_filter_lake_info(db_path, area_ths):

    sql_line = "select * from lake_location where lake_area > %.2f order by lake_id;" % area_ths

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql_line)
    result = cursor.fetchall()

    return result, len(result)


def get_ul_offset(db_path):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select ul_con_ridx, ul_con_cidx from geo_transform;")
    result = cursor.fetchone()
    conn.close()

    return result


def get_sub_basin_info(db_path, top_n_code, level):

    # 判断层级顺序是否正确
    top_n_level = len(top_n_code)
    if top_n_level >= level:
        raise RuntimeError("")

    table = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select code from %s where code like '%s';" % (table, top_n_code + "%"))
    result = cursor.fetchall()
    conn.close()

    return result


def update_many_alter_status(db_path, update_sql, update_val):
    """

    :param db_path:
    :param update_sql:
    :param update_val:
    :return:
    """

    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.executemany(update_sql, update_val)
    conn.commit()
    conn.close()


def insert_many_lake_id(db_path, insert_sql, insert_val):

    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.executemany(insert_sql, insert_val)
    conn.commit()
    conn.close()
    

def get_alter_basin_info(db_path, table_name):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select * from %s;" % table_name)
    result = cursor.fetchall()

    return result


def get_alter_lake_info(db_path, table_name):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select * from %s;" % table_name)
    result = cursor.fetchall()

    return result

