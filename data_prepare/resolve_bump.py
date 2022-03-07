import sys
import sqlite3
import numpy as np
sys.path.append("..")
from numba import jit
from util.raster import read_single_tif, array2tif
from basin.interface import label
from basin import db_op

"""
    目标：去除河流入海口处的凸出部分，使得海陆边界能够被一条入海河流正常地分为两段。
    step 1: 找出所有的凸出部分
    step 2: 统计并输出凸出部分（目前定义为入海口四邻域中面积最小的连通区）的信息，入库
    step 3: 人工检查凸出部分的选择是否合理
    step 4: 读取栅格数据（dir, upa, elv），去除凸起，并保存为新的栅格文件
"""

bump_table = "bump"
bump_sql = "INSERT INTO %s VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)" % bump_table


@jit(nopython=True)
def calc_all_label_num_and_upa(label_arr, upa_arr, num_result, upa_result):
    rows, cols = label_arr.shape
    for i in range(rows):
        for j in range(cols):
            label_val = label_arr[i, j]
            if label_val > 0:
                num_result[label_val] += 1
                upa_result[label_val] += upa_arr[i, j]
    return 1


def calc_diff_neighbor(a, b, c, d):
    src = np.array([a, b, c, d], dtype=np.uint32)
    uniq = np.unique(src)
    result = len(uniq)

    if uniq.__contains__(0):
        return result - 1
    else:
        return result


def create_bump_table(db_conn):
    """
    在数据库中建立凸起的表格
    :param db_conn:
    :return:
    """
    db_cursor = db_conn.cursor()
    # 在数据库中建立流域属性的表
    db_cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='%s';" % bump_table)
    exist_flag = db_cursor.fetchone()[0]
    # 如果表格已经存在，删除表格
    if exist_flag > 0:
        db_cursor.execute("DROP TABLE %s;" % bump_table)

    sql_line = '''CREATE TABLE %s
        (id INTEGER,
        ridx INTEGER,
        cidx INTEGER,
        u_label INTEGER,
        u_num INTEGER,
        u_area REAL,
        l_label INTEGER,
        l_num INTEGER,
        l_area REAL,
        r_label INTEGER,
        r_num INTEGER,
        r_area REAL,
        d_label INTEGER,
        d_num INTEGER,
        d_area REAL);''' % bump_table
    db_cursor.execute(sql_line)
    db_conn.commit()


def find_estuary_bump(dir_tif, upa_tif, min_threshold, bump_db):
    """

    :param dir_tif:
    :param upa_tif:
    :param min_threshold:
    :param bump_db:
    :return:
    """
    dir_arr, geo_trans, proj = read_single_tif(dir_tif)
    upa_arr, _, _ = read_single_tif(upa_tif)

    # 提取海陆边界
    all_edge = np.zeros(dir_arr.shape, dtype=np.uint8)
    all_edge[dir_arr == 0] = 1

    # 找到所有的出水口
    upa_arr[dir_arr != 0] = -9999
    outlets = np.argwhere(upa_arr > min_threshold)
    diff_neigh_num = np.zeros((outlets.shape[0],), dtype=np.int32)

    # 在出水口处打断海陆边界的连通性
    for loc_i, loc_j in outlets:
        all_edge[loc_i, loc_j] = 0

    # 四连通域分析
    edge_label_res, edge_label_num = label(all_edge)

    # 检查河流入海口是否将海陆边界划分成两个以上的部分
    p = 0
    for i, j in outlets:
        diff_neigh_num[p] = calc_diff_neighbor(edge_label_res[i - 1, j], edge_label_res[i, j - 1],
                                               edge_label_res[i, j + 1], edge_label_res[i + 1, j])
        p += 1

    # 统计每个label的数量和汇流面积
    label_num_arr = np.zeros(shape=(edge_label_num + 1,), dtype=np.uint32)
    label_upa_arr = np.zeros(shape=(edge_label_num + 1,), dtype=np.float32)
    calc_all_label_num_and_upa(edge_label_res, upa_arr, label_num_arr, label_upa_arr)

    # 创建数据库连接并创建表格
    conn = sqlite3.connect(bump_db)
    create_bump_table(conn)
    db_op.create_mo_table(conn)
    db_op.create_gt_table(conn)
    cursor = conn.cursor()

    # 插入地理参考数据
    gt_values = geo_trans + (0, 0) + dir_arr.shape
    cursor.execute(db_op.gt_sql, gt_values)
    conn.commit()

    # 插入入海口数据
    for ridx, cidx in outlets:
        mo_values = (int(ridx), int(cidx), float(upa_arr[ridx, cidx]))
        cursor.execute(db_op.mo_sql, mo_values)
    conn.commit()

    # 向数据库中中插入凸出的相关信息
    p = 1
    for i in range(outlets.shape[0]):
        if diff_neigh_num[i] > 2:
            y = int(outlets[i][0])
            x = int(outlets[i][1])
            u_label = int(edge_label_res[y - 1, x])
            u_num = int(label_num_arr[u_label])
            u_upa = float(label_upa_arr[u_label])
            l_label = int(edge_label_res[y, x - 1])
            l_num = int(label_num_arr[l_label])
            l_upa = float(label_upa_arr[l_label])
            r_label = int(edge_label_res[y, x + 1])
            r_num = int(label_num_arr[r_label])
            r_upa = float(label_upa_arr[r_label])
            d_label = int(edge_label_res[y + 1, x])
            d_num = int(label_num_arr[d_label])
            d_upa = float(label_upa_arr[d_label])
            cursor.execute(bump_sql, (
            p, y, x, u_label, u_num, u_upa, l_label, l_num, l_upa, r_label, r_num, r_upa, d_label, d_num, d_upa))
            p += 1

            # print("Location:(%d,%d); U:(%d,%d); L:(%d,%d); R(%d,%d); D(%d,%d); (%.6f,%.6f,%.6f,%.6f)" %
            #       (y, x, u_label, u_num, l_label, l_num, r_label, r_num, d_label, d_num, u_upa, l_upa, r_upa, d_upa))
    conn.commit()
    conn.close()


def get_transform(db_path):
    """
    从数据库中读取栅格数据的地理参考信息
    :param db_path:
    :return:
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    sql_line = "select lon, width, lon_rotate, lat, lat_rotate, height from %s;" % db_op.gt_table_name
    cursor.execute(sql_line)
    result = cursor.fetchone()
    conn.close()

    return result


def get_outlets(db_path):
    """
    从数据库中获取所有出水口信息
    :param db_path:
    :return:
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    sql_line = "select ridx, cidx from %s;" % db_op.mo_table_name
    cursor.execute(sql_line)
    result = cursor.fetchall()

    return result


def check_bump(bump_db):
    """

    :param bump_db:
    :return:
    """
    table_name = "bump"
    conn = sqlite3.connect(bump_db)
    cursor = conn.cursor()
    cursor.execute("select * from %s;" % table_name)
    bump_list = cursor.fetchall()
    conn.close()

    bump_num = len(bump_list)
    print(bump_num)
    # 计算每个bump面积最小的那一块
    num_list = np.zeros((bump_num,), dtype=np.int32)
    area_list = np.zeros((bump_num,), dtype=np.float32)
    nb_loc_list = np.zeros((bump_num,), dtype=np.int32)

    ul_lon, w, _, ul_lat, _, h = get_transform(bump_db)

    for i in range(bump_num):
        min_area = 99999999
        if min_area > bump_list[i][5] > 0:
            num_list[i] = bump_list[i][4]
            area_list[i] = bump_list[i][5]
            nb_loc_list[i] = 1
            min_area = bump_list[i][5]
        if min_area > bump_list[i][8] > 0:
            num_list[i] = bump_list[i][7]
            area_list[i] = bump_list[i][8]
            nb_loc_list[i] = 2
            min_area = bump_list[i][8]
        if min_area > bump_list[i][11] > 0:
            num_list[i] = bump_list[i][10]
            area_list[i] = bump_list[i][11]
            nb_loc_list[i] = 3
            min_area = bump_list[i][11]
        if min_area > bump_list[i][14] > 0:
            num_list[i] = bump_list[i][13]
            area_list[i] = bump_list[i][14]
            nb_loc_list[i] = 4
            min_area = bump_list[i][14]

    for i in range(bump_num):
        if num_list[i] > 1:
            y = bump_list[i][1]
            x = bump_list[i][2]
            lon = ul_lon + (x + 0.5) * w
            lat = ul_lat + (y + 0.5) * h
            print(lon, lat)
            # print(num_list[i], area_list[i])

    return bump_list, nb_loc_list


def resolve_bump(dir_tif, upa_tif, elv_tif, new_dir, new_upa, new_elv, bump_db):
    # 读取流向栅格数据
    dir_arr, geo_trans, proj = read_single_tif(dir_tif)

    # 提取海陆边界
    all_edge = np.zeros(dir_arr.shape, dtype=np.uint8)
    all_edge[dir_arr == 0] = 1

    # 读取outlet位置索引信息，并打断连通边
    outlets = get_outlets(bump_db)
    for idx_tuple in outlets:
        all_edge[idx_tuple] = 0

    # 四连通域分析
    edge_label_res, edge_label_num = label(all_edge)

    # 从数据库中查询凸出部分
    bump_list, nb_loc_list = check_bump(bump_db)
    bump_num = len(bump_list)

    # 计算有有多少海陆边界像元需要处理
    resolved_num = 0
    for i in range(bump_num):
        nb_dir = nb_loc_list[i]
        resolved_num += bump_list[i][3 * nb_dir + 1]

    # 计算待处理的海陆边界像元的位置索引
    resolved_idxs = np.zeros((resolved_num, 2), dtype=np.int32)

    def get_resolved_idx(loc_i, loc_j, nb):
        if nb == 1:
            return loc_i - 1, loc_j
        elif nb == 2:
            return loc_i, loc_j - 1
        elif nb == 3:
            return loc_i, loc_j + 1
        elif nb == 4:
            return loc_i + 1, loc_j
        else:
            raise RuntimeError("Unknown neighbour location %d!" % nb)

    # 提取需要消除的凸起部分
    p = 0
    for i in range(bump_num):
        sp = 3 * nb_loc_list[i] + 1
        if bump_list[i][sp] == 1:
            label_y, label_x = get_resolved_idx(bump_list[i][1], bump_list[i][2], nb_loc_list[i])
            resolved_idxs[p] = [label_y, label_x]
            p += 1
        elif bump_list[i][sp] > 1:
            label_y, label_x = get_resolved_idx(bump_list[i][1], bump_list[i][2], nb_loc_list[i])
            bump_label = edge_label_res[label_y, label_x]
            label_idxs = np.argwhere(edge_label_res == bump_label)
            resolved_idxs[p:p + label_idxs.shape[0]] = label_idxs
            p += label_idxs.shape[0]
        else:
            raise RuntimeError("label num %d not larger than 0!" % bump_list[sp + 1])

    # 流向栅格
    for i in range(resolved_num):
        y, x = resolved_idxs[i]
        dir_arr[y, x] = 247
    array2tif(new_dir, dir_arr, geo_trans, proj, nd_value=247, dtype=1)

    # 汇流累积量栅格
    upa_arr, geo_trans, proj = read_single_tif(upa_tif)
    for i in range(resolved_num):
        y, x = resolved_idxs[i]
        upa_arr[y, x] = -9999
    array2tif(new_upa, upa_arr, geo_trans, proj, nd_value=-9999, dtype=6)

    # 高程栅格
    elv_arr, geo_trans, proj = read_single_tif(elv_tif)
    for i in range(resolved_num):
        y, x = resolved_idxs[i]
        upa_arr[y, x] = -9999
    array2tif(new_elv, elv_arr, geo_trans, proj, nd_value=-9999, dtype=6)

    return 1


if __name__ == "__main__":

    src_dir = r"E:\BaiduNetdiskDownload\Asia\4\4_dir.tif"
    src_upa = r"E:\BaiduNetdiskDownload\Asia\4\4_upa.tif"
    src_elv = r"E:\BaiduNetdiskDownload\Asia\4\4_elv.tif"
    out_dir = r"E:\BaiduNetdiskDownload\Asia\4\4_new_dir.tif"
    out_upa = r"E:\BaiduNetdiskDownload\Asia\4\4_new_upa.tif"
    out_elv = r"E:\BaiduNetdiskDownload\Asia\4\4_new_elv.tif"

    river_threshold = 10
    bump_db_path = r"E:\BaiduNetdiskDownload\Asia\4\4_bump.db"

    find_estuary_bump(src_dir, src_upa, river_threshold, bump_db_path)
    check_bump(bump_db_path)
    # resolve_bump(src_dir, src_upa, src_elv, out_dir, out_upa, out_elv, bump_db_path)
