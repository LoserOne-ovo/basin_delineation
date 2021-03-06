from osgeo import gdal, ogr, osr
import os
import math
import numpy as np


cm_tif_opt = ["COMPRESS=DEFLATE", "NUM_THREADS=8", "BIGTIFF=IF_SAFER"]
dir_nodata = 247
upa_nodata = -9999
elv_nodata = -9999


class OType:
    Byte = 1
    U16 = 2
    I16 = 3
    U32 = 4
    I32 = 5
    F32 = 6
    F64 = 7


def read_tif_files(folder, code, sink_num):

    # 读取流向栅格数据
    ds = gdal.Open(os.path.join(folder, code + '_dir.tif'))
    geotransform = ds.GetGeoTransform()
    proj = ds.GetProjection()
    dir_arr = ds.ReadAsArray()

    # 读取汇流累积量栅格数据
    ds = gdal.Open(os.path.join(folder, code + '_upa.tif'))
    upa_arr = ds.ReadAsArray()

    elv_arr = None
    # 如果存在内流区，还需要读取高程数据
    if sink_num > 0:
        ds = gdal.Open(os.path.join(folder, code + '_elv.tif'))
        elv_arr = ds.ReadAsArray()

    return dir_arr, upa_arr, elv_arr, geotransform, proj


def array2tif(out_path, array, geotransform, proj, nd_value, dtype, opt=cm_tif_opt):
    """
    output an np.ndarray into a .tif file
    :param out_path:        out_put path of .tif file
    :param array:           np.ndarray
    :param geotransform:    geotransform
    :param proj:            projection in form of wkt
    :param nd_value:        no-data value
    :param dtype:           valid range [1,11] Byte, uint16, int16, uint32, int32, float32, float64 ...
    :param opt:             .tif create options
    :return:
    """

    gtiffDriver = gdal.GetDriverByName('GTiff')  # gtiffDriver = gdal.GetDriverByName(“MEM”)
    if gtiffDriver is None:
        raise ValueError("Can't find GeoTiff Driver")

    outDataSet = gtiffDriver.Create(out_path, array.shape[1], array.shape[0], 1, dtype, opt)
    outDataSet.SetGeoTransform(geotransform)
    outDataSet.SetProjection(proj)
    outband = outDataSet.GetRasterBand(1)
    outband.WriteArray(array, 0, 0)
    outband.SetNoDataValue(nd_value)
    outband.FlushCache()
    del outDataSet


def raster2shp(tif_path, shp_path):

    ds = gdal.Open(tif_path)
    src_band = ds.GetRasterBand(1)
    mask_band = src_band.GetMaskBand()
    proj = ds.GetProjection()

    drv = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = drv.CreateDataSource(shp_path)
    dst_layer = shp_ds.CreateLayer("pfafstetter", srs=osr.SpatialReference(wkt=proj))
    fd = ogr.FieldDefn("code", ogr.OFTInteger)
    dst_layer.CreateField(fd)

    gdal.Polygonize(src_band, mask_band, dst_layer, 0)
    shp_ds.Release()


def raster2shp_mem(shp_path, array, geotransform, proj, nd_value, dtype):


    gtiffDriver = gdal.GetDriverByName("MEM")
    outDataSet = gtiffDriver.Create("123", array.shape[1], array.shape[0], 1, dtype)
    outDataSet.SetGeoTransform(geotransform)
    outDataSet.SetProjection(proj)
    outband = outDataSet.GetRasterBand(1)
    outband.WriteArray(array, 0, 0)
    outband.SetNoDataValue(nd_value)
    mask_band = outband.GetMaskBand()

    drv = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = drv.CreateDataSource(shp_path)
    dst_layer = shp_ds.CreateLayer("1", srs=osr.SpatialReference(wkt=proj))
    fd = ogr.FieldDefn("code", ogr.OFTInteger)
    dst_layer.CreateField(fd)

    gdal.Polygonize(outband, mask_band, dst_layer, 0)
    shp_ds.Destroy()


def raster2vector_mem(array, geotransform, proj, nd_value, dtype):

    mem_raster_driver = gdal.GetDriverByName("MEM")
    memDataSet = mem_raster_driver.Create("temp", array.shape[1], array.shape[0], 1, dtype)
    memDataSet.SetGeoTransform(geotransform)
    memDataSet.SetProjection(proj)
    outband = memDataSet.GetRasterBand(1)
    outband.WriteArray(array, 0, 0)
    outband.SetNoDataValue(nd_value)
    mask_band = outband.GetMaskBand()

    mem_vector_dirver = ogr.GetDriverByName("MEMORY")
    mem_vector_ds = mem_vector_dirver.CreateDataSource("temp")
    dst_layer = mem_vector_ds.CreateLayer("1", srs=osr.SpatialReference(wkt=proj))
    fd = ogr.FieldDefn("code", ogr.OFTInteger)
    dst_layer.CreateField(fd)

    gdal.Polygonize(outband, mask_band, dst_layer, 0)

    return mem_vector_ds


def mask_whole_basin(tif_path):

    ds = gdal.Open(tif_path)
    geotransform = ds.GetGeoTransform()
    proj = ds.GetProjection()
    dir_arr = ds.ReadAsArray()
    dir_arr[dir_arr != 247] = 1
    dir_arr[dir_arr == 247] = 0

    return dir_arr, geotransform, proj


def mask_whole_basin_int32(tif_path):
    """

    :param tif_path:
    :return:
    """
    ds = gdal.Open(tif_path)
    geotransform = ds.GetGeoTransform()
    proj = ds.GetProjection()
    dir_arr = ds.ReadAsArray()

    basin_arr = np.zeros(shape=dir_arr.shape, dtype=np.int32)
    basin_arr[dir_arr == 247] = -9999

    return basin_arr, geotransform, proj


def read_single_tif(tif_path):

    if not os.path.exists(tif_path):
        raise IOError("Input tif file %s not found!" % tif_path)

    ds = gdal.Open(tif_path)
    geotransform = ds.GetGeoTransform()
    proj = ds.GetProjection()
    tif_arr = ds.ReadAsArray()

    return tif_arr, geotransform, proj


def cor2idx(lon, lat, gt):
    """

    :param lon:
    :param lat:
    :param gt:
    :return:
    """

    return (math.floor((lat-gt[3])/gt[5]),
            math.floor((lon-gt[0])/gt[1]))


def cor2idx_list(cor_list, geotrans):
    """

    :param cor_list:
    :param geotrans:
    :return:
    """

    return [cor2idx(lon, lat, geotrans) for lon,lat in cor_list]

