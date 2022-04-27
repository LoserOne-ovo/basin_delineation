from osgeo import gdal, ogr
import numpy as np


def create_bg(in_tif):

    ds = gdal.Open(in_tif)
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    geotransform = ds.GetGeoTransform()
    proj = ds.GetProjection()
    arr = np.zeros((rows, cols), dtype=np.int32)
    
    return arr, geotransform, proj


def rasterize_lake(lake_shp, rasterize_field, in_tif, out_tif):

    lake_ds = ogr.Open(lake_shp)
    if lake_ds is None:
        raise IOError("File %s does not exist!")
    lake_layer = lake_ds.GetLayer()

    lake_arr, geo_trans, proj = create_bg(in_tif)
    rows, cols = lake_arr.shape
    tif_options = ["COMPRESS=DEFLATE", "NUM_THREADS=8", "BIGTIFF=IF_SAFER"]
    tif_driver = gdal.GetDriverByName("GTiff")
    out_tif_ds = tif_driver.Create(out_tif, cols, rows, 1, gdal.GDT_Int32, tif_options)
    out_tif_ds.SetGeoTransform(geo_trans)
    out_tif_ds.SetProjection(proj)
    outband = out_tif_ds.GetRasterBand(1)
    outband.WriteArray(lake_arr, 0, 0)
    outband.SetNoDataValue(0)

    gdal.RasterizeLayer(out_tif_ds, [1], lake_layer, options=["ATTRIBUTE=%s" % rasterize_field])
    out_tif_ds.FlushCache()

    lake_ds.Destroy()


if __name__ == "__main__":


    lake_shp_path = r""
    burn_field_name = "LakeID"
    tif_path = r""
    out_path = r""
    rasterize_lake(lake_shp_path, burn_field_name, tif_path, out_path)



