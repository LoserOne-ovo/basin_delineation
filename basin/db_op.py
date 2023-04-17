import math
import sqlite3
import numpy as np


bp_table_name = 'property'
gt_table_name = 'geo_transform'
mo_table_name = 'outlets'
sk_table_name = 'sinks'
sr_table_name = 'regions'
is_table_name = 'islands'
cl_table_name = 'clusters'


bp_sql = "INSERT INTO property VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
gt_sql = "INSERT INTO geo_transform VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
mo_sql = "INSERT INTO outlets VALUES(?, ?, ?)"
sk_sql = "INSERT INTO sinks VALUES(?, ?, ?, ?)"
sr_sql = "INSERT INTO regions VALUES(?, ?, ?)"
is_sql = "INSERT INTO islands VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
cl_sql = "INSERT INTO clusters VALUES(?, ?, ?, ?)"


# 无需明确的id
# 按面积由大到小排序，可以由数据库查询实现
class Outlet:
    def __init__(self, dbRecord):
        self.loc = dbRecord[0:2]
        self.area = dbRecord[2]

    def morph(self, xOffset, yOffset):
        return self.loc[0] - xOffset, self.loc[1] - yOffset, self.area


# 通过location字段，分为mRegion和iRegion两类
# 按面积由大到小排序，可通过数据库查询实现
# sinks为一维numpy数组，存储sink_fid信息。sink_fid全局唯一。
class Region:
    def __init__(self, dbRecord):
        self.area = dbRecord[0]
        self.location = dbRecord[1]
        self.sinks = np.frombuffer(dbRecord[2], dtype=np.int32)

    def morph(self):
        return self.area, self.location, self.sinks.tobytes()


# fid全局唯一
# 严格按照面积由大到小排序插入数据库。
class Sink:
    def __init__(self, dbRecord):
        self.fid = dbRecord[0]
        self.area = dbRecord[1]
        self.loc = dbRecord[2:4]

    def morph(self, xOffset, yOffset):
        return self.fid, self.area, self.loc[0] - xOffset, self.loc[1] - yOffset


# 没有明确的id
# 按面积由大到小排序，可以由数据库查询实现
# islands为一维numpy数组，存储island_fid信息。sink_fid全局唯一。
class Cluster:
    def __init__(self, dbRecord):
        self.area = dbRecord[0]
        self.distance = dbRecord[1]
        self.mIsland = dbRecord[2]
        self.islands = np.frombuffer(dbRecord[3], dtype=np.int32)

    def morph(self):
        return self.area, self.distance, self.mIsland, self.islands.tobytes()


# fid全局唯一
# 严格按照面积由大到小排序插入数据库。
class Island:
    def __init__(self, dbRecord):
        self.fid = dbRecord[0]
        self.area = dbRecord[1]
        self.distance = dbRecord[2]
        self.iSample = dbRecord[3:5]
        self.mSample = dbRecord[5:7]
        self.type = dbRecord[7]

    def morph(self, xOffset, yOffset):
        return self.fid, self.area, self.distance, self.iSample[0] - xOffset, self.iSample[1] - yOffset, \
               self.mSample[0] - xOffset, self.mSample[1] - yOffset, self.type


########################################
#            Basin Property            #
########################################
def create_bp_table(db_Cursor):

    # 在数据库中建立流域属性的表
    db_Cursor.execute("DROP TABLE IF EXISTS %s;" % bp_table_name)
    sql_line = '''CREATE TABLE %s
        (type INTEGER,
        area REAL,
        total_area REAL,
        outlet_ridx INTEGER,
        outlet_cidx INTEGER,
        inlet_ridx INTEGER,
        inlet_cidx INTEGER,
        outlet_num INTEGER,
        region_num INTEGER,
        sink_num INTEGER,
        cluster_num INTEGER,
        island_num INTEGER,
        samples BLOB,
        clusterDstArr BLOB);''' % bp_table_name
    db_Cursor.execute(sql_line)


def insert_property(db_path, propertyValue):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_bp_table(cursor)
    cursor.execute(bp_sql, propertyValue)
    conn.commit()
    conn.close()


##########################################
#            Mainland Outlets            #
##########################################
def create_mo_table(db_Cursor):

    db_Cursor.execute("DROP TABLE IF EXISTS %s;" % mo_table_name)
    sql_line = '''CREATE TABLE %s
        (ridx INTEGER,
        cidx INTEGER,
        area REAL);''' % mo_table_name
    db_Cursor.execute(sql_line)


def insert_outlets(db_path, outletList):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_mo_table(cursor)
    cursor.executemany(mo_sql, outletList)
    conn.commit()
    conn.close()


###############################
#            Sinks            #
###############################
def create_sk_table(db_Cursor):

    db_Cursor.execute("DROP TABLE IF EXISTS %s;" % sk_table_name)
    sql_line = '''CREATE TABLE %s
        (fid INTEGER,
        area REAL,
        ridx INTEGER,
        cidx INTEGER);''' % sk_table_name
    db_Cursor.execute(sql_line)


def insert_sinks(db_path, sinkList):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_sk_table(cursor)
    cursor.executemany(sk_sql, sinkList)
    conn.commit()
    conn.close()


######################################
#            Sink Regions            #
######################################
def create_sr_table(db_Cursor):

    db_Cursor.execute("DROP TABLE IF EXISTS %s;" % sr_table_name)
    sql_line = '''CREATE TABLE %s
        (area REAL,
        location INTEGER,
        sinks BLOB);''' % sr_table_name
    db_Cursor.execute(sql_line)


def insert_regions(db_path, regionList):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_sr_table(cursor)
    cursor.executemany(sr_sql, regionList)
    conn.commit()
    conn.close()


#################################
#            Islands            #
#################################
def create_is_table(db_Cursor):

    db_Cursor.execute("DROP TABLE IF EXISTS %s;" % is_table_name)
    sql_line = '''CREATE TABLE %s
        (fid INTEGER,
        area REAL,
        distance REAL,
        sample_ridx INTEGER,
        sample_cidx INTEGER,
        dst_ridx INTEGER,
        dst_cidx INTEGER,
        type TINYINT);''' % is_table_name
    db_Cursor.execute(sql_line)


def insert_islands(db_path, islandList):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_is_table(cursor)
    cursor.executemany(is_sql, islandList)
    conn.commit()
    conn.close()


##################################
#            Clusters            #
##################################
def create_cl_table(db_Cursor):
    db_Cursor.execute("DROP TABLE IF EXISTS %s;" % cl_table_name)
    sql_line = '''CREATE TABLE %s
        (area REAL,
        distance REAL,
        nIsland_id INTEGER,
        island_id BLOB);''' % cl_table_name
    db_Cursor.execute(sql_line)


def insert_clusters(db_path, clusterList):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_cl_table(cursor)
    cursor.executemany(cl_sql, clusterList)
    conn.commit()
    conn.close()


##################################
#            Transform           #
##################################
def create_gt_table(db_Cursor):

    db_Cursor.execute("DROP TABLE IF EXISTS %s;" % gt_table_name)
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
    db_Cursor.execute(sql_line)


def insert_trans(db_path, transValue):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    create_gt_table(cursor)
    cursor.execute(gt_sql, transValue)
    conn.commit()
    conn.close()


###############################################
#            Level Basin Statistics           #
###############################################
def create_level_table(db_path, level):

    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS %s;" % table_name)

    sql_line = '''CREATE TABLE %s
        (src_code UNSIGNED BIG INT,
        code UNSIGNED BIG INT,
        down_code UNSIGNED BIG INT,
        type INTEGER,
        area REAL,
        total_area REAL,
        sink_num INTEGER,
        island_num INTEGER,
        outlet_lon REAL,
        outlet_lat REAL,
        inlet_lon REAL,
        inlet_lat REAL,
        ul_lon REAL,
        ul_lat REAL,
        cols INTEGER,
        rows INTEGER,
        width REAL,
        height REAL,
        divisible INTEGER);''' % table_name
    cursor.execute(sql_line)
    conn.commit()
    conn.close()


def insert_basin_stat(db_path, level, ins_value_list):
    table_name = "level_%d" % level
    sql_line = "INSERT INTO %s VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);" % table_name
    conn = sqlite3.connect(db_path, timeout=5)
    cursor = conn.cursor()
    cursor.executemany(sql_line, ins_value_list)
    conn.commit()
    conn.close()


######################################
#             数据查询                #
######################################

def get_basin_components(db_path):

    # 建立数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 读取流域属性数据
    cursor.execute("select * from %s;" % bp_table_name)
    basin_type, area, total_area, outlet_ridx, outlet_cidx, inlet_ridx, inlet_cidx, \
        outlet_num, region_num, sink_num, cluster_num, island_num, samples, clusterDstArr = cursor.fetchone()

    if samples is not None:
        samples = np.frombuffer(samples, dtype=np.int32).reshape((-1, 2))
    if clusterDstArr is not None:
        clusterDstArr = np.frombuffer(clusterDstArr, dtype=np.float32).reshape((cluster_num, cluster_num))

    # query information about mainland outlets
    if outlet_num <= 0:
        outlets = {}
    else:
        result = cursor.execute("select * from %s order by area desc;" % mo_table_name)
        outlets = {eid:Outlet(record) for eid, record in enumerate(result)}

    # query information about sink mRegions
    if region_num <= 0:
        mRegions = {}
        iRegions = {}
        mRegion_num = 0
        iRegion_num = 0
    else:
        result = cursor.execute("select * from %s where location=0 order by area desc;" % sr_table_name)
        mRegions = {eid:Region(record) for eid, record in enumerate(result)}
        mRegion_num = len(mRegions)
        result = cursor.execute("select * from %s where location<>0 order by area desc;" % sr_table_name)
        iRegions = {eid:Region(record) for eid, record in enumerate(result)}
        iRegion_num = len(iRegions)

    # query information about sinks
    if sink_num <= 0:
        sinks = {}
    else:
        result = cursor.execute("select * from %s order by fid asc;" % sk_table_name)
        sinks = {record[0]:Sink(record) for record in result}

    # query information about island clusters
    if cluster_num <= 0:
        clusters = {}
    else:
        result = cursor.execute("select * from %s order by area desc;" % cl_table_name)
        clusters = {eid:Cluster(record) for eid, record in enumerate(result)}

    # query information about islands
    if island_num <= 0:
        islands = {}
    else:
        result = cursor.execute("select * from %s order by fid asc;" % is_table_name)
        islands = {record[0]:Island(record) for record in result}

    return basin_type, area, total_area, (outlet_ridx, outlet_cidx), (inlet_ridx, inlet_cidx), \
        outlet_num, mRegion_num, iRegion_num, cluster_num, outlets, mRegions, iRegions, sinks, \
        clusters, islands, samples, clusterDstArr


def get_divisible_basins(db_path, level):
    """

    :param db_path:
    :param level:
    :return:
    """
    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select count(*), sum(total_area) from %s where divisible = 1;" % table_name)
    cur_num, cur_total_area = cursor.fetchone()

    sub_mean_area = cur_total_area / (3 * cur_num)
    divide_num = math.ceil(math.ceil(cur_total_area / sub_mean_area - cur_num) / 8)
    cursor.execute("select src_code, code, type, total_area from %s where divisible = 1 "
                   "order by total_area desc;" % table_name)
    basin_list = cursor.fetchall()
    conn.close()

    return basin_list, divide_num, cur_num


def get_divisible_basins_by_mae(db_path, level):
    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select count(*), sum(total_area) from %s where divisible = 1;" % table_name)
    divisible_num, total_area = cursor.fetchone()

    cursor.execute("select * from %s where divisible = 1 order by total_area desc;" % table_name)
    basin_list = cursor.fetchall()

    sub_mean_area = total_area / (3 * divisible_num)
    min_divide_num = math.ceil(math.ceil(total_area / sub_mean_area - divisible_num) / 8)
    max_divide_num = min(2 * min_divide_num + 2, divisible_num)

    if level >= 11:
        divide_num = divisible_num

    elif divisible_num > 1:
        cursor.execute("select total_area from %s where divisible = 1 order by total_area desc;" % table_name)
        areaList = cursor.fetchall()
        areaArr = np.array(areaList, dtype=np.float64).ravel()
        dAreaArr = np.empty((divisible_num * 9), dtype=np.float64)

        d_basin_num = divisible_num + min_divide_num * 8
        d_mean_area = total_area / d_basin_num
        for i in range(0, min_divide_num):
            dAreaArr[9 * i: 9 * i + 9] = areaArr[i] / 9
        dAreaArr[9 * min_divide_num:d_basin_num] = areaArr[min_divide_num:]
        tempArr = dAreaArr[0:d_basin_num]
        min_mae = np.sum(np.abs(tempArr - d_mean_area)) / d_basin_num
        divide_num = min_divide_num

        for j in range(min_divide_num, max_divide_num):
            d_basin_num = d_basin_num + 8
            d_mean_area = total_area / d_basin_num
            dAreaArr[j * 9:(j + 1) * 9] = areaArr[j] / 9
            dAreaArr[(j + 1) * 9:d_basin_num] = areaArr[j + 1:]
            tempArr = dAreaArr[0:d_basin_num]
            mae = np.sum(np.abs(tempArr - d_mean_area)) / d_basin_num
            if mae < min_mae:
                min_mae = mae
                divide_num = j + 1
            else:
                break
    else:
        divide_num = 1

    return basin_list, divide_num, divisible_num


def get_indivisible_basins(db_path, level):
    """

    :param db_path:
    :param level:
    :return:
    """
    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select * from %s where divisible = 0;" % table_name)
    basin_list = cursor.fetchall()
    conn.close()

    return basin_list, len(basin_list)


def get_level_basins(db_path, level):
    """

    :param db_path:
    :param level:
    :return:
    """
    table_name = "level_%d" % level
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select src_code, code, down_code, type, area, total_area, sink_num, island_num, outlet_lon,"
                   "outlet_lat, inlet_lon, inlet_lat from %s;" % table_name)
    basin_list = cursor.fetchall()
    conn.close()
    return basin_list


# def get_sub_basins(db_path, code, level):

    # table_name = "level_%d" % level
    # conn = sqlite3.connect(db_path)
    # cursor = conn.cursor()

    # code_length = len(str(code))
    # padding_zero_num = level - code_length
    # min_bound = code * 10 ** padding_zero_num
    # max_bound = min_bound + 10 ** padding_zero_num
    # cursor.execute("select * from %s where code > %d and code < %d';" % (table_name, min_bound, max_bound))
    # basin_list = cursor.fetchall()
    # conn.close()

    # return basin_list


def get_ul_offset(db_path):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select ul_con_ridx, ul_con_cidx, rows, cols from %s limit 1;" % gt_table_name)
    result = cursor.fetchone()
    conn.close()

    return result
