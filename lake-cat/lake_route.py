import sys
sys.path.append(r"../")
import time
import numpy as np
from util import raster
from util import interface as cfunc
from osgeo import gdal, ogr, osr


def get_route(lake_tif, dir_tif, upa_tif, out_path):

    # Read GeoTIFF data
    lake_arr, geotrans, proj = raster.read_single_tif(lake_tif)
    dir_arr, _, _ = raster.read_single_tif(dir_tif)
    upa_arr, _, _ = raster.read_single_tif(upa_tif)
    img_shape = lake_arr.shape
    ul_x, width, r_x, ul_y, r_y, height = geotrans
    srs = osr.SpatialReference(wkt=proj)
    lake_num = np.max(lake_arr)
    
    # Extract the flow path between lakes
    result, route_num = cfunc.create_route_between_lake_c(lake_arr, lake_num, dir_arr, upa_arr)
    
    # Create output shapefile
    driver = ogr.GetDriverByName("ESRI Shapefile")
    out_ds = driver.CreateDataSource(out_path)
    out_layer = out_ds.CreateLayer("route", srs=srs, geom_type=ogr.wkbLineString)
    UpLakeFieldDefn = ogr.FieldDefn("UpLake", ogr.OFTInteger)
    out_layer.CreateField(UpLakeFieldDefn)
    DownLakeFieldDefn = ogr.FieldDefn("DownLake", ogr.OFTInteger)
    out_layer.CreateField(DownLakeFieldDefn)
    featureDefn = out_layer.GetLayerDefn()
    
    offset = 0
    for i in range(route_num):
        # Get the length of current flow path
        route_length = int(result[offset + 2])
        offset += 3
        # Create linestring geometry for current flow path
        geometry = ogr.Geometry(ogr.wkbLineString)
        for j in range(route_length):
            idx_tuple = np.unravel_index(result[offset + j], img_shape)
            pX = ul_x + (idx_tuple[1] + 0.5) * width # longitude
            pY = ul_y + (idx_tuple[0] + 0.5) * height # latitude
            # Add point
            geometry.AddPoint(pX, pY)
        # Create feature for current flow path
        route_feature = ogr.Feature(featureDefn)
        route_feature.SetField("UpLake", int(result[offset + 0]))
        route_feature.SetField("DownLake", int(result[offset + 1]))
        route_feature.SetGeometry(geometry)
        out_layer.CreateFeature(route_feature)
        # move to next flow path
        offset += route_length

    out_layer.SyncToDisk()
    out_ds.Destroy()


if __name__ == "__main__":

    dir_tif_path = r""
    upa_tif_path = r""
    lake_tif_path = r""
    out_shp_path = r"E:\qyf\data\TP\route.shp"
    
    get_route(lake_tif_path, dir_tif_path, upa_tif_path, out_shp_path)
