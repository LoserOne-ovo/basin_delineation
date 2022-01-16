from osgeo import ogr
import os


"""
    将湖泊拆分到不同的shp文件中，一个shp对应一个湖泊
"""


def split_lake(lake_shp, out_folder):

    os.chdir(out_folder)
    shp_driver = ogr.GetDriverByName("ESRI Shapefile")

    lake_ds = ogr.Open(lake_shp)
    layer = lake_ds.GetLayer()
    srs = layer.GetSpatialRef()
    inLayerDefn = layer.GetLayerDefn()
    if layer.GetGeomType() != 3:
        raise RuntimeError("Unsupported input! The geometry type of lake should be polygon!")

    for feature in layer:

        lake_id = feature.GetField("Hylak_id")
        print(lake_id)
        out_name = str(lake_id) + ".shp"
        out_ds = shp_driver.CreateDataSource(out_name)
        out_layer = out_ds.CreateLayer("lake", srs=srs, geom_type=ogr.wkbPolygon)
        for i in range(0, inLayerDefn.GetFieldCount()):
            fieldDefn = inLayerDefn.GetFieldDefn(i)
            out_layer.CreateField(fieldDefn)

        geom = feature.GetGeometryRef()
        if geom.GetGeometryType() != 3:
            raise RuntimeError("Unsupported input! The geometry type of lake should be polygon!")
        total_area = geom.GetArea()
        sub_geom = geom.GetGeometryRef(0)
        sub_area = sub_geom.Area()
        if sub_area < total_area:
            raise RuntimeError("Invalid Polygon!")
        new_feature = feature.Clone()
        new_feature.SetGeometry(ogr.ForceToPolygon(sub_geom))
        out_layer.CreateFeature(new_feature)
        out_layer.SyncToDisk()
        out_ds.Destroy()

    lake_ds.Destroy()


if __name__ == "__main__":

    lake_shp_path = r"E:\qyf\data\Australia_multiprocess_test\lake\src_lake\au_lake_lt_2.shp"
    out_folder_path = r"E:\qyf\data\Australia_multiprocess_test\lake\single_lake"
    split_lake(lake_shp_path, out_folder_path)





