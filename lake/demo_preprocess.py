from osgeo import ogr
from multiprocessing import Pool
from file_op import get_basin_folder
from db_op import create_loc_table
import os
import sqlite3
import time


def get_geom(shp_fn):
    """
    读取流域Geometry
    :param shp_fn:
    :return:
    """

    ds = ogr.Open(shp_fn)
    layer = ds.GetLayer()
    geometry = ogr.Geometry(ogr.wkbMultiPolygon)

    for feature in layer:
        geom = feature.GetGeometryRef()
        geom_type = geom.GetGeometryType()
        if geom_type == 3:
            geometry.AddGeometry(geom)
        elif geom_type == 6:
            for sub_geom in geom:
                geometry.AddGeometry(sub_geom)
        else:
            raise RuntimeError("Unsupported Geometry Type %d in %s" % (geom_type, shp_fn))

    return geometry


def locate_lake(fid, lake_shp, root, top_code, lake_db, lv_limit):

    print(fid)
    ds = ogr.Open(lake_shp)
    layer = ds.GetLayer()
    feature = layer.GetFeature(fid)

    # 读取湖泊shp
    insert_list = ['-1'] * 18
    insert_list[0] = int(feature.GetField("Hylak_id"))
    insert_list[1] = float(feature.GetField("lake_area"))
    lake_geom = feature.GetGeometryRef()
    ds.Destroy()

    # 初始化第一层级
    loc_basin_code = top_code
    flag = True
    level = 1
    insert_list[level + 2] = loc_basin_code

    # 层级推进，寻找最小包含湖泊的流域
    while flag is True and level < lv_limit:
        level += 1
        for i in range(10):
            sub_code = loc_basin_code + str(i)
            flag = False
            sub_folder = get_basin_folder(root, sub_code)
            sub_shp = os.path.join(sub_folder, sub_code + ".shp")
            if os.path.exists(sub_shp):
                basin_geom = get_geom(sub_shp)
                flag = basin_geom.Contains(lake_geom)
                if flag is True:
                    loc_basin_code = sub_code
                    insert_list[level + 2] = loc_basin_code
                    break

    if flag is True:
        loc_level = level
    else:
        loc_level = level - 1
    insert_list[2] = loc_level

    # 向数据库中插入数据
    db_conn = sqlite3.connect(lake_db, timeout=30)
    db_cursor = db_conn.cursor()
    db_cursor.execute("INSERT INTO lake_location VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(insert_list))
    db_conn.commit()
    db_conn.close()


def main(root, top_code, lake_shp, lake_db, max_process_num, level_limit):
    """
    定位每一个湖泊到具体的流域，存到sqlite数据库中
    :param root: 按层级汇总的流域边界，每个层级一个文件夹，
                每个流域对应一个单独的shp。
    :param top_code:
    :param lake_shp: 大洲范围内筛选出的湖泊
    :param lake_db: 存放定位结果的数据库
    :param max_process_num:
    :param level_limit:
    :return:
    """

    create_loc_table(lake_db)
    in_ds = ogr.Open(lake_shp, 0)
    layer = in_ds.GetLayer()
    lake_num = layer.GetFeatureCount()
    in_ds.Destroy()

    pool = Pool(max_process_num)
    for i in range(lake_num):
        pool.apply_async(locate_lake, args=(i, lake_shp, root, top_code, lake_db, level_limit + 1))
    pool.close()
    pool.join()


if __name__ == "__main__":


    process_num = 8
    
    basin_project_root = r"E:\qyf\data\Australia_multiprocess_test"
    lake_shp_path = r"E:\qyf\data\Australia_multiprocess_test\lake\src_lake\au_lake_lt_2.shp"
    lake_db_path = r"E:\qyf\data\Australia_multiprocess_test\lake\lake_location.db"
    code = "7"

    max_level = 10

    time_start = time.time()
    main(basin_project_root, code, lake_shp_path, lake_db_path, process_num, max_level)
    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))
