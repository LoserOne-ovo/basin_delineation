import os
import sys
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
    parser = argparse.ArgumentParser(description="mosaic lake and lake slope into basin")
    parser.add_argument("basin_config", help="basin configuration file")
    parser.add_argument("lake_config", help="lake configuration file")
    parser.add_argument("level", help="level basin to burn lake hillslope", choices=range(1, 16), type=int)
    parser.add_argument("-m", "--method", help="whether to combine polygon with same hydro_id into a multipolygon", default=1, choices=[1, 2], type=int)
    args = parser.parse_args()

    basin_ini_file = args.basin_config
    lake_ini_file = args.lake_config

    p_root, level_db, min_ths = fp.parse_basin_ini(basin_ini_file)
    lake_db, alter_db, lake_folder, alter_folder = fp.parse_lake_ini(lake_ini_file)

    level = args.level
    method = args.method
    alter_folder = os.path.join(alter_folder, "level_%02d" % level)
    if not os.path.exists(alter_folder):
        os.mkdir(alter_folder)
    out_folder = os.path.join(p_root, "lake_result")
    if not os.path.exists(out_folder):
        os.mkdir(out_folder)
    
    return p_root, level_db, lake_db, alter_db, lake_folder, alter_folder, out_folder, level, method


def gather_shp_1(root, alter_db, alter_folder, level, loc_db, out_folder):
    
    shp_driver = ogr.GetDriverByName("ESRI Shapefile")
    out_shp = os.path.join(root, "lake_result", "level_%2d_v1.shp" % level)
    out_ds = shp_driver.CreateDataSource(out_shp)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    out_layer = out_ds.CreateLayer("lake", srs=srs, geom_type=ogr.wkbMultiPolygon)
    pidFieldDefn = ogr.FieldDefn("PFAF_ID", ogr.OFTString)
    pidFieldDefn.SetWidth(15)
    out_layer.CreateField(pidFieldDefn)
    typeFieldDefn = ogr.FieldDefn("TYPE", ogr.OFTInteger)
    out_layer.CreateField(typeFieldDefn)
    lidFieldDefn = ogr.FieldDefn("LAKE_ID", ogr.OFTInteger)
    out_layer.CreateField(lidFieldDefn)
    featureDefn = out_layer.GetLayerDefn()
    
    # 先读取basin要素
    basin_alter_info = dp.get_alter_basin_info(alter_db, level)
    for code, status in basin_alter_info:
        if status == 0:
            # 流域内没有湖泊和湖泊坡面
            basin_folder = fp.get_basin_folder(root, code)
            basin_shp = os.path.join(basin_folder, code + ".shp")
            in_ds = ogr.Open(basin_shp)
            in_layer = in_ds.GetLayer(0)
            # 构建geometry
            geometry = ogr.Geometry(ogr.wkbMultiPolygon)
            for feature in in_layer:
                geom = feature.GetGeometryRef()
                geometry.AddGeometry(geom)
            in_ds.Destroy()
            # 构建feature
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(geometry)
            feature.SetField("PFAF_ID", code)
            feature.SetField("TYPE", 1)
            feature.SetField("LAKE_ID", -9999)
            out_layer.CreateFeature(feature)
            
        elif status == 1:
            # 流域部分是湖泊和湖泊坡面
            basin_shp = os.path.join(alter_folder, "%s_bas_alt.shp" % code)
            in_ds = ogr.Open(basin_shp)
            in_layer = in_ds.GetLayer(0)            
            geometry = ogr.Geometry(ogr.wkbMultiPolygon)
            # 非湖泊和湖泊坡面的部分
            for feature in in_layer:
                geom = feature.GetGeometryRef()
                geometry.AddGeometry(geom)
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(geometry)
            feature.SetField("PFAF_ID", code)
            feature.SetField("TYPE", 1)
            feature.SetField("LAKE_ID", -9999)
            out_layer.CreateFeature(feature)
        else:
            # 流域全部都是湖泊和湖泊坡面
            continue

    # 再读取湖泊和湖泊坡面要素
    lake_alter_info = dp.get_alter_lake_info(alter_db, level)
    for basin_code, lake_id in lake_alter_info:
        lake_shp = os.path.join(alter_folder, "%d_lak_alt.shp" % lake_id)
        in_ds = ogr.Open(lake_shp)
        in_layer = in_ds.GetLayer(0)
        
        geometry = ogr.Geometry(ogr.wkbMultiPolygon)
        in_layer.SetAttributeFilter("TYPE=2")
        for feature in in_layer:
            geom = feature.GetGeometryRef()
            geometry.AddGeometry(geom)
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(geometry)
        feature.SetField("PFAF_ID", basin_code)
        feature.SetField("TYPE", 2)
        feature.SetField("LAKE_ID", lake_id)
        out_layer.CreateFeature(feature)
        
        geometry = ogr.Geometry(ogr.wkbMultiPolygon)
        in_layer.SetAttributeFilter("TYPE=3")
        for feature in in_layer:
            geom = feature.GetGeometryRef()
            geometry.AddGeometry(geom)
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(geometry)
        feature.SetField("PFAF_ID", basin_code)
        feature.SetField("TYPE", 3)
        feature.SetField("LAKE_ID", lake_id)
        out_layer.CreateFeature(feature)

    out_layer.SyncToDisk()
    out_ds.Destroy()


def gather_shp_2(root, alter_db, alter_folder, level, loc_db, out_folder):

    shp_driver = ogr.GetDriverByName("ESRI Shapefile")
    out_shp = os.path.join(out_folder, "level_%2d_v2.shp" % level)
    out_ds = shp_driver.CreateDataSource(out_shp)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    out_layer = out_ds.CreateLayer("lake", srs=srs, geom_type=ogr.wkbMultiPolygon)
    pidFieldDefn = ogr.FieldDefn("PFAF_ID", ogr.OFTString)
    pidFieldDefn.SetWidth(15)
    out_layer.CreateField(pidFieldDefn)
    typeFieldDefn = ogr.FieldDefn("TYPE", ogr.OFTInteger)
    out_layer.CreateField(typeFieldDefn)
    lidFieldDefn = ogr.FieldDefn("LAKE_ID", ogr.OFTInteger)
    out_layer.CreateField(lidFieldDefn)
    featureDefn = out_layer.GetLayerDefn()

    # 先读取basin要素
    basin_alter_info = dp.get_alter_basin_info(alter_db, level)
    for code, status in basin_alter_info:
        if status == 0:
            # 流域内没有湖泊和湖泊坡面
            basin_folder = fp.get_basin_folder(root, code)
            basin_shp = os.path.join(basin_folder, code + ".shp")
            in_ds = ogr.Open(basin_shp)
            in_layer = in_ds.GetLayer(0)
            # 构建feature
            for feature in in_layer:
                geom = feature.GetGeometryRef()
                feature = ogr.Feature(featureDefn)
                feature.SetGeometry(geom)
                feature.SetField("PFAF_ID", code)
                feature.SetField("TYPE", 1)
                feature.SetField("LAKE_ID", -9999)
                out_layer.CreateFeature(feature)
            in_ds.Destroy()

        elif status == 1:
            # 流域部分是湖泊和湖泊坡面
            basin_shp = os.path.join(alter_folder, "%s_bas_alt.shp" % code)
            in_ds = ogr.Open(basin_shp)
            in_layer = in_ds.GetLayer(0)
            for feature in in_layer:
                out_layer.CreateFeature(feature)
            in_ds.Destroy()
        else:
            # 流域全部都是湖泊和湖泊坡面
            continue

    # 再读取湖泊和湖泊坡面要素
    lake_alter_info = dp.get_alter_lake_info(alter_db, level)
    for basin_code, lake_id in lake_alter_info:
        lake_shp = os.path.join(alter_folder, "%d_lak_alt.shp" % lake_id)
        in_ds = ogr.Open(lake_shp)
        in_layer = in_ds.GetLayer(0)
        for feature in in_layer:
            out_layer.CreateFeature(feature)
        in_ds.Destroy()

    # 释放内存
    out_layer.SyncToDisk()
    out_ds.Destroy()


def main(root, alter_db, alter_folder, level, loc_db, out_folder, method):
    if method == 1:
        gather_shp_1(root, alter_db, alter_folder, level, loc_db, out_folder)
    else:
        gather_shp_2(root, alter_db, alter_folder, level, loc_db, out_folder)


if __name__ == "__main__":

    time_start = time.time()
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_start)))
    basin_project_root, level_db_path, lake_db_path, alter_db_path, lake_shp_folder, alter_shp_folder, result_shp_folder, p_level, p_method  = create_args()
    main(basin_project_root, alter_db_path, alter_shp_folder, p_level, lake_db_path, result_shp_folder, p_method)
    time_end = time.time()
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_end)))
    print("total time consumption: %.2f s!" % (time_end - time_start))



