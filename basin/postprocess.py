import os
import time
import argparse
import db_op as dp
import file_op as fp
from osgeo import ogr, osr


def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="Gather all sub-basin shp at the same level into a shapefile.")
    parser.add_argument("config", help="configuration file")
    parser.add_argument("level", help="the level of sub-basin shp that you want to gather", type=int, choices=range(1, 15))
    parser.add_argument("-m", "--method", help="whether to combine polygon with same hyfro_id into a multipolygon", default=1, choices=[1, 2], type=int)
    parser.add_arg
    args = parser.parse_args()

    ini_file = args.config
    if not os.path.isfile(ini_file):
        raise RuntimeError("Configuration file does not exist!")

    # 配置文件中要读取三个参数
    tgt_args = ["project_root", "level_database", "minimum_river_threshold"]
    ini_dict = {}
    with open(ini_file, "r") as fs:
        line = fs.readline()
        while line:
            line_str = line.split("=")
            if line_str[0] in tgt_args:
                ini_dict[line_str[0]] = line_str[1]
            line = fs.readline()
    fs.close()

    flag = True
    # 检查项目根目录参数
    if tgt_args[0] in ini_dict.keys():
        p_root = ini_dict[tgt_args[0]].strip()
        if not os.path.exists(p_root):
            print("The path of %s does not exist!" % tgt_args[0])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[0])
        flag = False
    # 检查汇总数据库参数
    if tgt_args[1] in ini_dict.keys():
        level_db = ini_dict[tgt_args[1]].strip()
        if not os.path.isdir(os.path.dirname(level_db)):
            print("The path of %s does not exist!" % tgt_args[1])
            flag = False
    else:
        print("%s not found in the config file!" % tgt_args[1])
        flag = False
    # 检查河网阈值
    if tgt_args[2] in ini_dict.keys():
        min_ths = ini_dict[tgt_args[2]].strip()
        if not check_float(min_ths):
            print("%s could not be converted to a float!" % tgt_args[2])
            flag = False
        else:
            min_ths = float(min_ths)
            if min_ths <= 0.:
                print("%s must be larger than 0!" % tgt_args[2])
                flag = False
    else:
        print("%s not found in the config file!" % tgt_args[2])

        flag = False

    if flag is False:
        exit(-1)
    level = args.level

    return p_root, level_db, min_ths, level


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


def gather_basin_shp_1(root, level_db, level)
    """
    Gather all sub-basin shp at the same level into a shapefile.
    :param root:
    :param level_db:
    :param level:
    :return:
    """
    # 查询当前层级有哪些流域
    basin_list = dp.get_level_basins(level_db, level)
    # 输出文件名
    out_folder = os.path.join(root, "shp_result")
    if not os.path.exists(out_folder):
        os.mkdir(out_folder)
    out_shp = os.path.join(out_folder, "level_%d_v1.shp" % level)

    # 创建输出shp
    driver = ogr.GetDriverByName('ESRI Shapefile')
    out_ds = driver.CreateDataSource(out_shp)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    out_layer = out_ds.CreateLayer(out_shp, srs, ogr.wkbMultiPolygon)
    pidFieldDefn = ogr.FieldDefn("PFAF_ID", ogr.OFTString)
    pidFieldDefn.SetWidth(15)
    out_layer.CreateField(pidFieldDefn)
    featureDefn = out_layer.GetLayerDefn()
    
    # 将每一个流域所有的geometry合并成一个Multipolygon
    # 注意，合并后的MultiPolygon可能会自交，所以无法用于地理处理
    for record in basin_list:
        code = record[0]
        basin_folder = fp.get_basin_folder(root, code)
        shp_path = os.path.join(basin_folder, code + ".shp")
        if not os.path.exists(shp_path):
            raise IOError("Missing %s!" % shp_path)
        in_ds = driver.Open(shp_path, 0)
        layer = in_ds.GetLayer()
        
        new_geometry = ogr.Geometry(ogr.wkbMultiPolygon)
        for feature in layer:
            geom = feature.GetGeometryRef()
            new_geometry.AddGeometry(geom)
        in_ds.Destroy()

        out_feature = ogr.Feature(featureDefn)
        out_feature.SetGeometry(new_geometry)
        out_feature.SetField("PFAF_ID", code)
        out_layer.CreateFeature(out_feature)

    out_layer.SyncToDisk()
    out_ds.Destroy()


def gather_basin_shp_2(root, level_db, level):
    """
    Gather all sub-basin shp at the same level into a shapefile.
    :param root:
    :param level_db:
    :param level:
    :return:
    """
    # 查询当前层级有哪些流域
    basin_list = dp.get_level_basins(level_db, level)
    # 输出文件名
    out_folder = os.path.join(root, "shp_result")
    if not os.path.exists(out_folder):
        os.mkdir(out_folder)
    out_shp = os.path.join(out_folder, "level_%d_v2.shp" % level)

    # 创建输出shp
    driver = ogr.GetDriverByName('ESRI Shapefile')
    out_ds = driver.CreateDataSource(out_shp)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    out_layer = out_ds.CreateLayer(out_shp, srs, ogr.wkbMultiPolygon)
    pidFieldDefn = ogr.FieldDefn("PFAF_ID", ogr.OFTString)
    pidFieldDefn.SetWidth(15)
    out_layer.CreateField(pidFieldDefn)
    featureDefn = out_layer.GetLayerDefn()

    # 将每一个流域所有的feature复制到结果图层
    # 注意，一个流域在结果图层中可能对应读个feature
    for record in basin_list:
        code = record[0]
        basin_folder = fp.get_basin_folder(root, code)
        shp_path = os.path.join(basin_folder, code + ".shp")
        if not os.path.exists(shp_path):
            raise IOError("Missing %s!" % shp_path)
        in_ds = driver.Open(shp_path, 0)
        layer = in_ds.GetLayer()
        for feature in layer:
            out_feature = ogr.Feature(featureDefn)
            out_feature.SetGeometry(feature.GetGeometryRef())
            out_feature.SetField("PFAF_ID", code)
            out_layer.CreateFeature(out_feature)
        in_ds.Destroy()

    out_layer.SyncToDisk()
    out_ds.Destroy()


def main(root, level_db, level, method):

    if method == 1:
        gather_basin_shp_1(root, level_db, level)
    else:
        gather_basin_shp_2(root, level_db, level)


if __name__ == "__main__":

    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    time_start = time.time()

    # 解析参数
    project_root, level_database, minimum_river_threshold, process_level = create_args()
    # 业务函数
    gather_basin_shp(project_root, level_database, process_level)

    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))





