import gc
import sys
sys.path.append(r"../../")
import pickle
import sqlite3
import numpy as np
from numba import jit
from util import raster
from util import interface as cfunc


"""
    目标：去除河流入海口处的凸出部分，使得海陆边界能够被一条入海河流正常地分为两段。
    step 1: 找出所有的凸出部分
    step 2: 统计并输出凸出部分（目前定义为入海口四邻域中面积最小的连通区）的信息，入库
    step 3: 人工检查凸出部分的选择是否合理
    step 4: 读取栅格数据（dir, upa, elv），去除凸起，并保存为新的栅格文件
"""


bump_table = "bump"
bump_sql = "INSERT INTO %s VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)" % bump_table


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
        d_area REAL,
        bump BLOB);''' % bump_table
    db_cursor.execute(sql_line)
    db_conn.commit()


@jit(nopython=True)
def calc_all_label_num_and_upa(label_arr, upa_arr, num_result, upa_result):
    """
    计算每个四连通区域的像元数量和总的汇流累积量
    :param label_arr:
    :param upa_arr:
    :param num_result:
    :param upa_result:
    :return:
    """
    rows, cols = label_arr.shape
    for i in range(rows):
        for j in range(cols):
            label_val = label_arr[i, j]
            if label_val > 0:
                num_result[label_val] += 1
                upa_result[label_val] += upa_arr[i, j]
    return 1


def calc_diff_neighbor(a, b, c, d):
    """
    计算4个值中，除0外的互不相等的值的数量
    :param a:
    :param b:
    :param c:
    :param d:
    :return:
    """
    src = np.array([a, b, c, d], dtype=np.uint32)
    uniq = np.unique(src)
    result = len(uniq)

    if uniq.__contains__(0):
        return result - 1
    else:
        return result


def get_bump_idxs(label_arr, bump_label, center_i, center_j, radius):

    rows, cols = label_arr.shape
    min_ridx = max(0, center_i - radius)
    min_cidx = max(0, center_j - radius)
    max_ridx = min(rows, center_i + radius)
    max_cidx = min(cols, center_j + radius)
    result = np.argwhere(label_arr[min_ridx:max_ridx, min_cidx:max_cidx] == bump_label)
    
    # 检查凸起部是否完全位于缓冲区内
    a = np.sum(result[:, 0] == 0)
    b = np.sum(result[:, 0] == (max_ridx - min_ridx))
    c = np.sum(result[:, 1] == 0)
    d = np.sum(result[:, 1] == (max_cidx - min_cidx))
    
    if (a + b + c + d) == 0:
        result[:, 0] += min_ridx
        result[:, 1] += min_cidx
        result = result.astype(np.uint64)
        result = result[:, 0] * cols + result[:, 1]
        return result
    else:
        if min_ridx == 0 and min_cidx == 0 and max_ridx == rows and max_cidx == cols:
            return -1
        else:
            return 0


def find_estuary_bump(dir_tif, upa_tif, min_threshold, bump_db):
    """
    找到所有的河流入海口，统计四邻域信息，并存入数据库
    :param dir_tif:
    :param upa_tif:
    :param min_threshold:
    :param bump_db:
    :return:
    """

    ####################################
    #    用河流入海口将海岸线打断成若干段    #
    ####################################
    # 读取栅格数据
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif)
    upa_arr, _, _ = raster.read_single_tif(upa_tif)
    # 提取海陆边界
    all_edge = np.zeros(dir_arr.shape, dtype=np.uint8)
    all_edge[dir_arr == 0] = 1
    # 找到所有的出水口
    upa_arr[dir_arr != 0] = -9999
    del dir_arr
    gc.collect()
    outlets = np.argwhere(upa_arr > min_threshold)
    diff_neigh_num = np.zeros((outlets.shape[0],), dtype=np.int32)
    # 在出水口处打断海陆边界的连通性
    for loc_i, loc_j in outlets:
        all_edge[loc_i, loc_j] = 0
    # 四连通域分析
    edge_label_res, edge_label_num = cfunc.label(all_edge)
    del all_edge
    gc.collect()

    ###############################
    #    计算河流入海口四邻域的信息    #
    ###############################
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
    del upa_arr
    gc.collect()

    ################
    #    数据入库    #
    ################
    # 创建数据库连接并创建表格
    conn = sqlite3.connect(bump_db)
    create_bump_table(conn)
    cursor = conn.cursor()
    
    ul_lon, w, _, ul_lat, _, h = geo_trans
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
               
            bump_loc = 0
            bump_label = 0
            bump_idx_num = 0
            # 面积最小的凸出部
            min_area = 99999999
            if min_area > u_upa > 0:
                bump_label = u_label
                bump_loc = 1
                bump_idx_num = u_num
                min_area = u_upa
            if min_area > l_upa > 0:
                bump_label = l_label
                bump_loc = 2
                bump_idx_num = l_num
                min_area = l_upa
            if min_area > r_upa > 0:
                bump_label = r_label
                bump_loc = 3
                bump_idx_num = r_num
                min_area = r_upa
            if min_area > d_upa > 0:
                bump_label = d_label
                bump_loc = 4
                bump_idx_num = d_num
                min_area = d_upa
            if bump_loc == 0 or bump_label == 0:
                raise RuntimeError("Can't find a bump at(%d,%d)" % (y, x))
            
            lon = ul_lon + (x + 0.5) * w
            lat = ul_lat + (y + 0.5) * h
            # 输出凸出部面积最小的连通区的信息
            if bump_idx_num > 1:
                if bump_loc == 1:
                    print(lon, lat, u_num, u_upa)
                elif bump_loc == 2:
                    print(lon, lat, l_num, l_upa)       
                elif bump_loc == 3:
                    print(lon, lat, r_num, r_upa)
                else:
                    print(lon, lat, d_num, d_upa)
            
            radius = 1000
            bump_idxs = get_bump_idxs(edge_label_res, bump_label, y, x, radius)
            while isinstance(bump_idxs, int):
                if bump_idxs == 0:
                    radius *= 2
                    bump_idxs = get_bump_idxs(edge_label_res, bump_label, y, x, radius)
                else:
                    raise RuntimeError("Input dir .tif is too narrow!")
            
            
            cursor.execute(bump_sql, (
            p, y, x, u_label, u_num, u_upa, l_label, l_num, l_upa, r_label, r_num, r_upa, d_label, d_num, d_upa, pickle.dumps(bump_idxs)))
            p += 1

            # print("Location:(%d,%d); U:(%d,%d); L:(%d,%d); R(%d,%d); D(%d,%d); (%.6f,%.6f,%.6f,%.6f)" %
            #       (y, x, u_label, u_num, l_label, l_num, r_label, r_num, d_label, d_num, u_upa, l_upa, r_upa, d_upa))
    conn.commit()
    conn.close()


def resolve_bump_old(dir_tif, upa_tif, elv_tif, new_dir, new_upa, new_elv, bump_db):
    """
    去除河流入海口处的凸起
    :param dir_tif:
    :param upa_tif:
    :param elv_tif:
    :param new_dir:
    :param new_upa:
    :param new_elv:
    :param bump_db:
    :return:
    """
    # 读取流向栅格数据
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif)

    # 提取海陆边界
    all_edge = np.zeros(dir_arr.shape, dtype=np.uint8)
    all_edge[dir_arr == 0] = 1
    # 读取outlet位置索引信息，并打断连通边
    outlets = get_outlets(bump_db)
    for idx_tuple in outlets:
        all_edge[idx_tuple] = 0

    # 四连通域分析
    edge_label_res, edge_label_num = cfunc.label(all_edge)
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


    ###################################
    #    去除凸起，并保存为新的栅格文件    #
    ###################################
    # 流向栅格
    for i in range(resolved_num):
        y, x = resolved_idxs[i]
        dir_arr[y, x] = 247
    raster.array2tif(new_dir, dir_arr, geo_trans, proj, nd_value=raster.dir_nodata, dtype=raster.OType.Byte)
    # 汇流累积量栅格
    dir_arr, geo_trans, proj = raster.read_single_tif(upa_tif)
    for i in range(resolved_num):
        y, x = resolved_idxs[i]
        dir_arr[y, x] = -9999
    raster.array2tif(new_upa, dir_arr, geo_trans, proj, nd_value=raster.upa_nodata, dtype=raster.OType.F32)
    # 高程栅格
    dir_arr, geo_trans, proj = raster.read_single_tif(elv_tif)
    for i in range(resolved_num):
        y, x = resolved_idxs[i]
        dir_arr[y, x] = -9999
    raster.array2tif(new_elv, dir_arr, geo_trans, proj, nd_value=raster.elv_nodata, dtype=raster.OType.F32)

    return 1


def resolve_bump(src_dir, in_mask, out_mask, bump_db):

    conn = sqlite3.connect(bump_db)
    cursor = conn.cursor()
    cursor.execute("select bump from %s;" % bump_table)
    result = cursor.fetchall()
    conn.close()

    # 读取流向栅格数据
    dir_arr, geo_trans, proj = raster.read_single_tif(src_dir)
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    mask_arr, _, _ = raster.read_single_tif(in_mask)

    for record in result:
        idxs = pickle.loads(record[0])
        colors = np.zeros(shape=idxs.shape, dtype=np.uint8)
        cfunc.paint_up_uint8(idxs, colors, re_dir_arr, mask_arr)
        
    raster.array2tif(out_mask, mask_arr, geo_trans, proj, nd_value=0, dtype=raster.OType.Byte)


if __name__ == "__main__":

    merge_dir = r"E:\qyf\data\Europe\merge\Europe_dir.tif"
    merge_upa = r"E:\qyf\data\Europe\merge\Europe_upa.tif"
    src_mask = r"E:\qyf\data\Europe\merge\Europe_dir_track_1.tif"
    upd_mask = r"E:\qyf\data\Europe\merge\Europe_mask.tif"

    river_threshold = 10
    bump_db_path = r"E:\qyf\data\Europe\merge\2_bump.db"

    # 先检查凸起，不运行resolve_bump
    # find_estuary_bump(merge_dir, merge_upa, river_threshold, bump_db_path)

    # 人工检验后，去除bump
    resolve_bump(merge_dir, src_mask, upd_mask, bump_db_path)


    # 确定没有问题后，再单独运行resolve_bump
    # resolve_bump(src_dir, src_upa, src_elv, out_dir, out_upa, out_elv, bump_db_path)
