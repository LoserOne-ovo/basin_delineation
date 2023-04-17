import os
import time
import argparse
import db_op as dp
import file_op as fp
from osgeo import ogr, osr


FieldDict = {
    "Basin_ID": ogr.OFTInteger64,
    "Down_ID": ogr.OFTInteger64,
    "Type": ogr.OFTInteger,
    "Hylak_id": ogr.OFTInteger,
    "Endor": ogr.OFTInteger,
    "Outlet_lon": ogr.OFTReal,
    "outlet_lat": ogr.OFTReal,
    "Area": ogr.OFTReal
}


def create_args():
    """
    Parsing command line parameters and the configuration file.
    :return:
    """
    parser = argparse.ArgumentParser(description="divide basins of a given level into sub basins at next level")
    parser.add_argument("config", help="configuration file")
    parser.add_argument("level", help="level basin to be divided", type=int, choices=range(1, 15))
    parser.add_argument("-f", "--format", default="shp", choices=["gdb", "shp", "gpkg"], type=str,
                        help="output format of the specific level basins, whether 'shp', 'gpkg' or 'gdb'.")
    args = parser.parse_args()

    level = args.level
    out_format = args.format
    p_root, basin_db, alter_db, lake_shp, min_ths, code, src_code = fp.parse_lake_ini(args.config)

    return p_root, alter_db, code, level, out_format


def get_basin_geom_1(src_code, root):

    # 流域边界文件
    str_src_code = str(src_code)
    folder = os.path.join(root, *str_src_code)
    fn = os.path.join(folder, "%s.shp" % str_src_code)

    # 获取流域边界矢量
    inDs = ogr.Open(fn)
    inLayer = inDs.GetLayer(0)
    fNum = inLayer.GetFeatureCount()
    if fNum == 1:
        feature = inLayer.GetFeature(0)
        geom = feature.GetGeometryRef()
        out_geom = ogr.ForceToMultiPolygon(geom)
    else:
        out_geom = ogr.Geometry(ogr.wkbMultiPolygon)
        for feature in inLayer:
            geom = feature.GetGeometryRef()
            out_geom.AddGeometry(geom)
        out_geom = out_geom.UnionCascaded()
    inDs.Destroy()

    return out_geom


def get_basin_geom_2(code, sub_code, folder):

    fn = os.path.join(folder, "%d.shp" % code)
    inDs = ogr.Open(fn)
    inLayer = inDs.GetLayer(0)
    inLayer.SetAttributeFilter("BASIN_ID=%d" % sub_code)
    feature = inLayer.GetNextFeature()
    inGeom = feature.GetGeometryRef()
    out_geom = inGeom.Clone()
    inDs.Destroy()

    return out_geom


def GetDriver(out_format):

    if out_format == "shp":
        return ogr.GetDriverByName("ESRI Shapefile")
    elif out_format == "gdb":
        return ogr.GetDriverByName("FileGDB")
    elif out_format == "gpkg":
        return ogr.GetDriverByName("GPKG")
    else:
        return None


def create_vector(basinList, lakeList, root, level, top_code,
                  alter_basin_folder, alter_lake_folder, out_fn, out_fmt):

    # ABBC_YYYYYYYY
    # A代表大洲
    # BB代表层级
    # C代表类型， 1代表流域，2代表湖泊，3代表湖泊坡面

    # 先给每个子流域一个唯一的标识
    basinTagDict = {}
    lakeTagDict = {}

    basin_pre_value = (1000 * top_code + level * 10 + 1) * 10**8
    suf_basin_id = 1
    for basinInfo in basinList:
        src_tag = tuple(basinInfo[0:2])
        basinTagDict[src_tag] = basin_pre_value + suf_basin_id
        suf_basin_id += 1

    lake_pre_value = (1000 * top_code + level * 10 + 2) * 10**8
    suf_lake_id = 1
    for lakeInfo in lakeList:
        src_tag = lakeInfo[0]
        lakeTagDict[src_tag] = lake_pre_value + suf_lake_id
        suf_lake_id += 1

    # driver = ogr.GetDriverByName("ESRI Shapefile")
    driver = GetDriver(out_fmt)
    ds = driver.CreateDataSource(out_fn)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    layer = ds.CreateLayer("data", srs=srs, geom_type=ogr.wkbMultiPolygon)
    for key, value in FieldDict.items():
        fieldDefn = ogr.FieldDefn(key, value)
        layer.CreateField(fieldDefn)
    featureDefn = layer.GetLayerDefn()

    for basinInfo in basinList:
        code, sub_code, down_code, down_sub_code, down_lake_fid, btype, \
            outlet_lon, outlet_lat, u_status, src_code = basinInfo

        # 子流域范围不被湖泊水库所影响，那么读取原来的流域范围
        if u_status == 0:
            out_geom = get_basin_geom_1(src_code, root)
        # 否则，读取更新后的流域范围
        else:
            out_geom = get_basin_geom_2(code, sub_code, alter_basin_folder)
        # 生成新的流域要素
        if out_geom.GetGeometryType() == ogr.wkbPolygon:
            out_geom = ogr.ForceToMultiPolygon(out_geom)
        out_feature = ogr.Feature(featureDefn)
        out_feature.SetGeometry(out_geom)
        # 流域编号
        src_tag = (code, sub_code)
        new_tag = basinTagDict[src_tag]
        out_feature.SetField("Basin_ID", new_tag)
        # 下游编号
        if down_lake_fid >= 0:
            down_tag = lakeTagDict[down_lake_fid]
        elif down_code <= 0:
            down_tag = down_code
        else:
            src_down_tag = (down_code, down_sub_code)
            down_tag = basinTagDict[src_down_tag]
        out_feature.SetField("Down_ID", down_tag)
        # 类型
        out_feature.SetField("Type", 1)
        # 内流标识
        endor_flag = 1 if down_code == -1 else 0
        out_feature.SetField("Endor", endor_flag)
        # 流域出水口经度
        if outlet_lon is not None:
            out_feature.SetField("Outlet_lon", outlet_lon)
        # 流域出水口纬度
        if outlet_lat is not None:
            out_feature.SetField("Outlet_lat", outlet_lat)
        # 创建要素
        layer.CreateFeature(out_feature)

    # 湖泊和湖泊坡面
    for lakeInfo in lakeList:
        fid, lake_id, down_code, down_sub_code, btype, outlet_lon, outlet_lat = lakeInfo
        fn = os.path.join(alter_lake_folder, "%d.shp" % fid)
        inDs = ogr.Open(fn)
        inLayer = inDs.GetLayer(0)

        # 湖泊
        inFeature = inLayer.GetFeature(0)
        out_geom = inFeature.GetGeometryRef()
        if out_geom.GetGeometryType() == ogr.wkbPolygon:
            out_geom = ogr.ForceToMultiPolygon(out_geom)
        out_feature = ogr.Feature(featureDefn)
        out_feature.SetGeometry(out_geom)
        # 编号
        new_tag = lakeTagDict[fid]
        out_feature.SetField("Basin_ID", new_tag)
        # 下游编号
        if down_code <= 0:
            down_tag = down_code
        else:
            src_down_tag = (down_code, down_sub_code)
            down_tag = basinTagDict[src_down_tag]
        out_feature.SetField("Down_ID", down_tag)
        # 类型
        out_feature.SetField("Type", 2)
        # Hylak_id编号
        out_feature.SetField("Hylak_id", lake_id)
        # 内流标识
        endor_flag = 1 if btype == 3 else 0
        out_feature.SetField("Endor", endor_flag)
        # 流域出水口经度
        if outlet_lon is not None:
            out_feature.SetField("Outlet_lon", outlet_lon)
        # 流域出水口纬度
        if outlet_lat is not None:
            out_feature.SetField("Outlet_lat", outlet_lat)
        layer.CreateFeature(out_feature)

        # 湖泊坡面
        # 湖泊
        inFeature = inLayer.GetFeature(1)
        out_geom = inFeature.GetGeometryRef()
        if out_geom.GetGeometryType() == ogr.wkbPolygon:
            out_geom = ogr.ForceToMultiPolygon(out_geom)
        out_feature = ogr.Feature(featureDefn)
        out_feature.SetGeometry(out_geom)
        # 编号
        new_tag = lakeTagDict[fid] + 10**8
        out_feature.SetField("Basin_ID", new_tag)
        # 下游编号
        down_tag = lakeTagDict[fid]
        out_feature.SetField("Down_ID", down_tag)
        # 类型
        out_feature.SetField("Type", 3)
        # 内流标识
        endor_flag = 0
        out_feature.SetField("Endor", endor_flag)
        layer.CreateFeature(out_feature)

    # 释放内存
    layer.SyncToDisk()
    ds.Destroy()


def workflow(alter_db, level, root, top_code, out_fmt):

    lake_out_folder = os.path.join(root, "lake_alter", "level_%d" % level, "lake")
    basin_out_folder = os.path.join(root, "lake_alter", "level_%d" % level, "basin")

    out_folder = os.path.join(root, "lake_result", out_fmt)
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    out_fn = os.path.join(out_folder, "level_%d.%s" % (level, out_fmt))

    basinResult = dp.get_basin_status(alter_db, level)
    lakeResult = dp.get_lake_status(alter_db, level)

    create_vector(basinResult, lakeResult, root, level, top_code, basin_out_folder, lake_out_folder, out_fn, out_fmt)


def main():
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    time_start = time.time()

    # 解析参数
    root, alter_db, top_code, level, out_format = create_args()
    # 业务函数
    workflow(alter_db, level, root, top_code, out_format)

    time_end = time.time()
    print("total time consumption: %.2f s!" % (time_end - time_start))


if __name__ == "__main__":
    main()
