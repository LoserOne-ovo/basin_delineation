import os
import sys
from osgeo import ogr, osr
from db_op import get_alter_basin_info, get_alter_lake_info
from file_op import get_basin_folder


def gather_shp(root, alter_db, alter_folder, level, out_folder):

    shp_driver = ogr.GetDriverByName("ESRI Shapefile")
    out_shp = os.path.join(out_folder, "level_%2d.shp" % level)
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
    basin_alter_info = get_alter_basin_info(alter_db, level)
    for code, status in basin_alter_info:

        if status == 0:
            # 流域内没有湖泊和湖泊坡面
            basin_folder = get_basin_folder(root, code)
            basin_shp = os.path.join(basin_folder, code + ".shp")
            in_ds = ogr.Open(basin_shp)
            in_layer = in_ds.GetLayer(0)

            # 构建geometry
            geometry = ogr.Geometry(ogr.wkbMultiPolygon)
            for feature in in_layer:
                geom = feature.GetGeometryRef
                geom_type = geom.GetGeometryType()
                if geom_type == 3:
                    geometry.AddGeometry(geom)
                elif geom_type == 6:
                    for sub_geom in geom:
                        geometry.AddGeometry(sub_geom)
                else:
                    raise RuntimeError("Unsupported Geometry Type %d!" % geom_type)
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

            for feature in in_layer:
                out_layer.CreateFeature(feature.Clone())
            in_ds.Destroy()

        else:
            # 流域全部都是湖泊和湖泊坡面
            continue


    # 再读取湖泊和湖泊坡面要素
    lake_alter_info = get_alter_lake_info(alter_db, level)
    for info in lake_alter_info:

        lake_shp = os.path.join(alter_folder, "%d_lak_alt.shp" % info[0])
        in_ds = ogr.Open(lake_shp)
        in_layer = in_ds.GetLayer(0)

        for feature in in_layer:
            out_layer.CreateFeature(feature.Clone())
        in_ds.Destroy()


    out_layer.SyncToDisk()
    out_ds.Destroy()




if __name__ == "__main__":


    max_level = 10
    p_level = int(sys.argv[1])
    if p_level < 4 or p_level > max_level:
        print("level must be between 4 and %d" % max_level)
        exit(-1)

    basin_root = r""
    alter_db_path = r""
    alter_shp_folder = r""
    result_folder = r""











