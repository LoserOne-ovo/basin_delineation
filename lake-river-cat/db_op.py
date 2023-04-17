import sqlite3


location_table = "lake_location"
location_insert_sql = "INSERT INTO lake_location VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
bp_table_name = 'basin_property'
gt_table_name = 'geo_transform'
mo_table_name = 'main_outlets'
sb_table_name = 'sink_bottoms'
is_table_name = 'islands'


class SubBasin:
    def __init__(self, record):
        self.code = record[0]
        self.sub_code = record[1]
        self.down_code = record[2]
        self.down_sub_code = record[3]
        self.down_lake = record[4]
        self.btype = record[5]
        self.outlet_lon = record[6]
        self.outlet_lat = record[7]
        self.status = record[8]
        self.src_code = record[9]

    def export(self):
        return (self.code, self.sub_code, self.down_code, self.down_sub_code, self.down_lake,
                self.btype, self.outlet_lon, self.outlet_lat, self.status, self.src_code)


class Lake:
    def __init__(self, record):
        self.fid = record[0]
        self.down_code = record[1]
        self.down_sub_code = record[2]
        self.btype = record[3]
        self.outlet_lon = record[4]
        self.outlet_lat = record[5]
        self.lake_id = record[6]



def create_alter_table(db_path, level):
    """

    :param db_path:
    :param level:
    :return:
    """
    # 子流域
    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS %s;" % table_name)
    sqline = '''CREATE TABLE %s
        (code UNSIGNED BIG INT,
        sub_code INTEGER,
        down_code BIG INT,
        down_sub_code INTEGER,
        down_lake INTEGER,
        btype SMALLINT,
        outlet_lon REAL,
        outlet_lat REAL,
        status TINYINT,
        src_code UNSIGNED BIG INT);''' % table_name
    cursor.execute(sqline)

    # 湖泊
    table_name = "lake_level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS %s;" % table_name)
    sqline = '''CREATE TABLE %s
        (fid INTEGER,
        lake_id INTEGER,
        down_code BIG INT,
        down_sub_code INTEGER,
        outlet_lon REAL,
        outlet_lat REAL,
        type TINYINT);''' % table_name
    cursor.execute(sqline)

    conn.commit()
    conn.close()


def insert_basin_info(db_path, level, insert_val):

    table_name = "level_%d" % level
    insert_sql = "INSERT INTO %s VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);" % table_name
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executemany(insert_sql, insert_val)
    conn.commit()
    conn.close()


def insert_lake_info(db_path, level, insert_val):
    """

    :param db_path:
    :param level:
    :param insert_val:
    :return:
    """
    table_name = "lake_level_%d" % level
    insert_sql = "INSERT INTO %s VALUES(?, ?, ?, ?, ?, ?, ?);" % table_name
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executemany(insert_sql, insert_val)
    conn.commit()
    conn.close()


def get_basin_status(db_path, level):

    table_name = "level_%d" % level
    sql_line = "select * from %s where status>=0;" % table_name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql_line)
    result = cursor.fetchall()

    conn.close()
    return result


def get_lake_status(db_path, level):

    table_name = "lake_level_%d" % level
    sql_line = "select * from %s;" % table_name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql_line)
    result = cursor.fetchall()

    conn.close()
    return result


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


#######################
#    流域属性信息查询    #
#######################
def get_ul_offset(db_path):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select ul_con_ridx, ul_con_cidx, rows, cols from %s limit 1;" % gt_table_name)
    result = cursor.fetchone()
    conn.close()

    return result


def get_sub_basin_info(db_path, basin_code, sub_level):
    """

    :param db_path:
    :param basin_code:
    :param sub_level:
    :return:
    """

    # 判断层级顺序是否正确

    src_level = len(str(basin_code))
    if src_level >= sub_level:
        raise RuntimeError("level of input basin is lower than given sub-level!")

    table = "level_%d" % sub_level

    Lower_boundary = basin_code * 10 ** (sub_level - src_level)
    Upper_boundary = (basin_code + 1) * 10 ** (sub_level - src_level)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select src_code, code, down_code, type, outlet_lon, outlet_lat, inlet_lon, inlet_lat from %s "
                   "where code >= %d and code < %d;" %
                   (table, Lower_boundary, Upper_boundary))
    result = cursor.fetchall()
    conn.close()

    return result


def get_mean_basin_area(db_path, level):

    table_name = "level_%d" % level
    sql_line = "select avg(area) from %s;" % table_name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql_line)
    result = cursor.fetchone()

    conn.close()
    return result[0]