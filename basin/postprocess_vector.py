import os
import time
import argparse
import db_op as dp
import file_op as fp
from osgeo import ogr, osr


fieldDict = {"Pfaf_ID": ogr.OFTInteger64,
             "Down_ID": ogr.OFTInteger64,
             "Type": ogr.OFTInteger,
             "Area": ogr.OFTReal,
             "Total_Area": ogr.OFTReal,
             "Endor_Num": ogr.OFTInteger,
             "Island_Num":ogr.OFTInteger,
             "Outlet_lon": ogr.OFTReal,
             "Outlet_lat": ogr.OFTReal,
             "Inlet_lon": ogr.OFTReal,
             "Inlet_lat": ogr.OFTReal}


def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="Gather all sub-basin shp at the same level into a shapefile.")
    parser.add_argument("config", help="configuration file")
    parser.add_argument("level", help="the level of sub-basin shp that you want to gather",
                        type=int, choices=range(1, 13))
    parser.add_argument("-f", "--format", default="shp", choices=["gdb", "shp", "gpkg"], type=str,
                        help="output format of the specific level basins, whether 'shp', 'gpkg' or 'gdb'.")

    args = parser.parse_args()
    p_root, level_db, min_ths = fp.parse_basin_ini(args.config)
    level = args.level
    out_format = args.format

    return p_root, level_db, min_ths, level, out_format


def GetDriver(out_format):

    if out_format == "shp":
        return ogr.GetDriverByName("ESRI Shapefile")
    elif out_format == "gdb":
        return ogr.GetDriverByName("FileGDB")
    elif out_format == "gpkg":
        return ogr.GetDriverByName("GPKG")
    else:
        return None


def gather_basin_feature(root, level_db, level, out_format):

    # 生成输出目录
    out_folder = os.path.join(root, "basin_result", out_format)
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    basinList = dp.get_level_basins(level_db, level)
    driver = GetDriver(out_format)
    out_fn = os.path.join(out_folder, "level_{}.{}".format(str(level), out_format))

    # 创建输出shp
    out_ds = driver.CreateDataSource(out_fn)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    out_layer = out_ds.CreateLayer("data", srs, geom_type=ogr.wkbMultiPolygon)
    for key, value in fieldDict.items():
        fieldDefn = ogr.FieldDefn(key, value)
        out_layer.CreateField(fieldDefn)
    featureDefn = out_layer.GetLayerDefn()

    # 将每一个流域所有的geometry合并成一个Multipolygon
    # 注意，合并后的MultiPolygon可能会自交，所以无法用于地理处理
    for info in basinList:
        src_code = str(info[0])
        shp_path = os.path.join(root, *src_code, src_code + ".shp")
        if not os.path.exists(shp_path):
            raise IOError("Missing %s!" % shp_path)
        in_ds = ogr.Open(shp_path, 0)
        layer = in_ds.GetLayer()
        fNum = layer.GetFeatureCount()
        if fNum == 1:
            feature = layer.GetFeature(0)
            geom = feature.GetGeometryRef()
            new_geometry = ogr.ForceToMultiPolygon(geom)
            # new_geometry = feature.GetGeometryRef()
        else:
            new_geometry = ogr.Geometry(ogr.wkbMultiPolygon)
            for feature in layer:
                geom = feature.GetGeometryRef()
                new_geometry.AddGeometry(geom)
            new_geometry = new_geometry.UnionCascaded()
        in_ds.Destroy()

        out_feature = ogr.Feature(featureDefn)
        out_feature.SetGeometry(new_geometry)
        for probe, key in enumerate(fieldDict.keys(), 1):
            out_feature.SetField(key, info[probe])
        out_layer.CreateFeature(out_feature)

    out_layer.SyncToDisk()
    out_ds.Destroy()

    return 1


def main():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    time_start = time.time()

    # 解析参数
    project_root, level_database, minimum_river_threshold, process_level, out_format = create_args()
    # 业务函数
    gather_basin_feature(project_root, level_database, process_level, out_format)

    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))


if __name__ == "__main__":
    main()
