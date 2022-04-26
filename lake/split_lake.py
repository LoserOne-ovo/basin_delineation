import os
from osgeo import ogr


def split_lake(lake_shp, out_folder):
    """
    将湖泊拆分到不同的shp文件中，一个shp对应一个湖泊。
    同时应该确保每个湖泊只有一个Polygon，不含岛（洞）。
    这里使用的数据来自于HydroLakes。
    :param lake_shp:
    :param out_folder:
    :return:
    """

    shp_driver = ogr.GetDriverByName("ESRI Shapefile")
    lake_ds = ogr.Open(lake_shp)
    layer = lake_ds.GetLayer()
    srs = layer.GetSpatialRef()
    inLayerDefn = layer.GetLayerDefn()
    if layer.GetGeomType() != 3:
        raise RuntimeError("Unsupported input! The geometry type of lake should be polygon!")

    os.chdir(out_folder)
    for feature in layer:
        lake_id = feature.GetField("Hylak_id")
        print(lake_id)
        out_name = str(lake_id) + ".shp"
        out_ds = shp_driver.CreateDataSource(out_name)
        out_layer = out_ds.CreateLayer("lake", srs=srs, geom_type=ogr.wkbPolygon)
        # 复制属性字段定义
        for i in range(0, inLayerDefn.GetFieldCount()):
            fieldDefn = inLayerDefn.GetFieldDefn(i)
            out_layer.CreateField(fieldDefn)

        geom = feature.GetGeometryRef()
        if geom.GetGeometryType() == 3:
            total_area = geom.GetArea()
            # 去除内部的岛(洞)
            sub_geom = geom.GetGeometryRef(0)
            sub_area = sub_geom.GetArea()
            # 检查去除操作是否正确
            if sub_area < total_area:
                raise RuntimeError("Invalid Polygon!")
            new_feature = feature.Clone()
            new_feature.SetGeometry(ogr.ForceToPolygon(sub_geom))
            out_layer.CreateFeature(new_feature)
        elif geom.GetGeometryType() == 6:
            new_geometry = ogr.Geometry(ogr.wkbMultiPolygon)
            for s_geom in geom:
                total_area = s_geom.GetArea()
                # 去除内部的岛(洞)
                sub_geom = s_geom.GetGeometryRef(0)
                sub_area = sub_geom.GetArea()
                if sub_area < total_area:
                    raise RuntimeError("Invalid Polygon!")
                new_geometry.AddGeometry(ogr.ForceToPolygon(sub_geom))
            new_feature = feature.Clone()
            new_feature.SetGeometry(new_geometry)
            out_layer.CreateFeature(new_feature)
        else:
            raise RuntimeError("Unsupported input! The geometry type of lake should be polygon or multipolygon!")
        out_layer.SyncToDisk()
        out_ds.Destroy()

    lake_ds.Destroy()


if __name__ == "__main__":

    lake_shp_path = r"E:\qyf\data\Australia\lake\Au_lake_1km2.shp"
    out_folder_path = r"E:\qyf\data\Australia\lake\splite"
    split_lake(lake_shp_path, out_folder_path)





