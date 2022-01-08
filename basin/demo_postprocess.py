from osgeo import ogr, osr
import os
import sys
from db_op import get_level_basins
from file_op import get_basin_folder


def gather_basin_shp(root, out_folder, out_pre, db_path, level):

    table = "level_" + str(level)
    basin_list = get_level_basins(db_path, table)

    driver = ogr.GetDriverByName('ESRI Shapefile')
    out_shp = os.path.join(out_folder, out_pre + "_level_%02d.shp" % level)

    out_ds = driver.CreateDataSource(out_shp)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    out_layer = out_ds.CreateLayer(out_shp, srs, ogr.wkbMultiPolygon)
    pidFieldDefn = ogr.FieldDefn("PFAF_ID", ogr.OFTInteger64)
    out_layer.CreateField(pidFieldDefn)
    featureDefn = out_layer.GetLayerDefn()

    for record in basin_list:
        code = record[0]
        basin_folder = get_basin_folder(root, code)
        shp_path = os.path.join(basin_folder, code + ".shp")
        if not os.path.exists(shp_path):
            raise IOError("Missing %s!" % shp_path)
        in_ds = driver.Open(shp_path, 0)
        layer = in_ds.GetLayer()
        layer_geomtype = layer.GetGeomType()

        new_geometry = ogr.Geometry(ogr.wkbMultiPolygon)

        if layer_geomtype == 3:
            for feature in layer:
                geom = feature.GetGeometryRef()
                new_geometry.AddGeometry(geom)
        elif layer_geomtype == 6:
            for feature in layer:
                geom = feature.GetGeometryRef()
                for sub_geom in geom:
                    new_geometry.AddGeometry(sub_geom)
        else:
            raise ValueError("Unexpected GeometryType")

        in_ds.Destroy()

        out_feature = ogr.Feature(featureDefn)
        out_feature.SetGeometry(new_geometry)
        out_feature.SetField("PFAF_ID", int(code))
        out_layer.CreateFeature(out_feature)
        out_feature = None

    out_layer.SyncToDisk()
    out_ds.Destroy()


if __name__ == "__main__":

    root_folder = r"E:\qyf\data\Australia_multiprocess_test"
    stat_db_path = r"E:\qyf\data\Australia_multiprocess_test\statistic.db"
    out_folder = r"E:\qyf\data\Australia_multiprocess_test\result"
    out_shp_pre = "au"

    level_str = sys.argv[1]
    level = int(level_str)
    
    gather_basin_shp(root_folder, out_folder, out_shp_pre, stat_db_path, level)

    print("done!")






