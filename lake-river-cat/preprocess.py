import os
import time
import db_op as dp
import file_op as fp
from osgeo import ogr
from multiprocessing import Pool



def check_overlap(basin_shp, lake_geom):
    """
    判断湖泊是否完全被当前流域包含
    :param basin_shp:
    :param lake_geom
    :return:
    """
    # 读取流域shp
    ds = ogr.Open(basin_shp)
    layer = ds.GetLayer()
    for feature in layer:
        geom = feature.GetGeometryRef()
        if geom.Overlaps(lake_geom):
            return True
    return False


def check_contain(basin_shp, lake_geom):
    """
    判断湖泊是否完全被当前流域包含
    :param basin_shp:
    :param lake_geom
    :return:
    """
    # 读取流域shp
    ds = ogr.Open(basin_shp)
    layer = ds.GetLayer()
    for feature in layer:
        geom = feature.GetGeometryRef()
        if geom.Contains(lake_geom):
            return True
    return False


def locate_lake(fid, lake_shp, root, top_code, lake_db, lv_limit):

    ds = ogr.Open(lake_shp)
    layer = ds.GetLayer()
    feature = layer.GetFeature(fid)

    # 读取某一个湖泊shp
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
        flag = False
        for i in range(10):
            sub_code = loc_basin_code + str(i)
            sub_folder = fp.get_basin_folder(root, sub_code)
            sub_shp = os.path.join(sub_folder, sub_code + ".shp")
            if os.path.exists(sub_shp):
                flag = check_contain(sub_shp, lake_geom)
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
    dp.insert_location_info(lake_db, tuple(insert_list))


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

    dp.create_loc_table(lake_db)
    in_ds = ogr.Open(lake_shp, 0)
    layer = in_ds.GetLayer()
    lake_num = layer.GetFeatureCount()
    in_ds.Destroy()

    pool = Pool(max_process_num)
    for i in range(lake_num):
        pool.apply_async(locate_lake_2, args=(i, lake_shp, root, top_code, lake_db, level_limit))
    pool.close()
    pool.join()


def locate_lake_2(fid, lake_shp, root, top_code, lake_db, lv_limit):

    ds = ogr.Open(lake_shp)
    layer = ds.GetLayer()
    feature = layer.GetFeature(fid)
    print(fid)
    # 读取某一个湖泊shp
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
        flag = False
        for i in range(10):
            sub_code = loc_basin_code + str(i)
            sub_folder = fp.get_basin_folder(root, sub_code)
            if os.path.exists(sub_folder):
                sub_shp = os.path.join(sub_folder, sub_code + ".shp")
                sub_db = os.path.join(sub_folder, sub_code + ".db")
                sub_type = dp.get_basin_type(sub_db)
                if sub_type == 2:
                    continue
                flag = check_contain(sub_shp, lake_geom)
                if flag is True:
                    loc_basin_code = sub_code
                    insert_list[level + 2] = loc_basin_code
                    break

    if flag is True:
        loc_level = level
    else:
        loc_level = level - 1

    # 如果没有落在第二层级流域内，检查以下情况
    if loc_level == 1:
        # 检查是否是某一部分落在海上，即虽然没有包某一个流域包含，但是只与一个流域相交
        temp_overlap = []
        for i in range(10):
            sub_code = loc_basin_code + str(i)
            sub_folder = fp.get_basin_folder(root, sub_code)
            sub_shp = os.path.join(sub_folder, sub_code + ".shp")
            if os.path.exists(sub_shp):
                flag = check_overlap(sub_shp, lake_geom)
                if flag is True:
                    temp_overlap.append(sub_code)
        if len(temp_overlap) == 1:
            loc_level = 2
            insert_list[4] = temp_overlap[0]
 
    insert_list[2] = loc_level
    # 向数据库中插入数据
    dp.insert_location_info(lake_db, tuple(insert_list))


if __name__ == "__main__":

    process_num = 8
    max_level = 10
    code = "7"
    basin_shp_root = r"E:\qyf\data\Australia"
    lake_shp_path = r"E:\qyf\data\Australia\lake\Au_lake_1km2.shp"
    lake_db_path = r"E:\qyf\data\Australia\lake\Au_lake_location.db"

    time_start = time.time()
    main(basin_shp_root, code, lake_shp_path, lake_db_path, process_num, max_level)
    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))
