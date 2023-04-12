from osgeo import gdal, ogr, osr
import os
import math


cm_tif_opt = ["COMPRESS=DEFLATE", "NUM_THREADS=8", "BIGTIFF=IF_SAFER"]
dir_nodata = 247
upa_nodata = -9999.0
elv_nodata = -9999.0


class OType:
    Byte = 1
    U16 = 2
    I16 = 3
    U32 = 4
    I32 = 5
    F32 = 6
    F64 = 7


def read_single_tif(tif_path):

    if not os.path.exists(tif_path):
        raise IOError("Input tif file %s not found!" % tif_path)

    ds = gdal.Open(tif_path)
    geo_trans = ds.GetGeoTransform()
    proj = ds.GetProjection()
    tif_arr = ds.ReadAsArray()

    return tif_arr, geo_trans, proj


def read_tif_files(root, sink_num, cur_basin_tif, ul_offset_info):

    row_offset, col_offset, rows, cols = ul_offset_info
    raster_folder = os.path.join(root, "raster")

    # 读取当前流域的掩膜数据
    ds = gdal.Open(cur_basin_tif)
    geo_trans = ds.GetGeoTransform()
    proj = ds.GetProjection()
    band = ds.GetRasterBand(1)
    mask_arr = band.ReadAsArray()
    mask = mask_arr == 0
    # 读取流向栅格数据
    dirTifPath = os.path.join(raster_folder, "dir.tif")
    ds = gdal.Open(dirTifPath)
    band = ds.GetRasterBand(1)
    dir_arr = band.ReadAsArray(col_offset, row_offset, cols, rows)
    dir_arr[mask] = dir_nodata

    # 读取汇流累积量栅格数据
    upaTifPath = os.path.join(raster_folder, "upa.tif")
    ds = gdal.Open(upaTifPath)
    band = ds.GetRasterBand(1)
    upa_arr = band.ReadAsArray(col_offset, row_offset, cols, rows)
    upa_arr[mask] = upa_nodata

    # 如果存在内流区，还需要读取高程数据
    if sink_num > 0:
        elvTifPath = os.path.join(raster_folder, "elv.tif")
        ds = gdal.Open(elvTifPath)
        band = ds.GetRasterBand(1)
        elv_arr = band.ReadAsArray(col_offset, row_offset, cols, rows)
        elv_arr[mask] = elv_nodata
    else:
        elv_arr = None

    return dir_arr, upa_arr, elv_arr, geo_trans, proj


def array2tif(out_path, array, geo_trans, proj, nd_value, dtype, opt=cm_tif_opt):
    """
    output an np.ndarray into a .tif file
    :param out_path:        out_put path of .tif file
    :param array:           np.ndarray
    :param geo_trans:       geotransform
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
    outDataSet.SetGeoTransform(geo_trans)
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
    dst_layer = shp_ds.CreateLayer("1", srs=osr.SpatialReference(wkt=proj))
    fd = ogr.FieldDefn("code", ogr.OFTInteger)
    dst_layer.CreateField(fd)

    gdal.Polygonize(src_band, mask_band, dst_layer, 0)
    shp_ds.Release()


def output_basin_tif(work_folder, cur_code, array, geo_trans, proj):

    tif_path = os.path.join(work_folder, "%d.tif" % cur_code)
    shp_path = os.path.join(work_folder, "%d.shp" % cur_code)

    gtiffDriver = gdal.GetDriverByName('GTiff')
    if gtiffDriver is None:
        raise ValueError("Can't find GeoTiff Driver")

    outDataSet = gtiffDriver.Create(tif_path, array.shape[1], array.shape[0], 1, 1, cm_tif_opt)
    outDataSet.SetGeoTransform(geo_trans)
    outDataSet.SetProjection(proj)
    outband = outDataSet.GetRasterBand(1)
    outband.WriteArray(array, 0, 0)
    outband.SetNoDataValue(0)
    outband.FlushCache()
    mask_band = outband.GetMaskBand()

    shp_drv = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = shp_drv.CreateDataSource(shp_path)
    dst_layer = shp_ds.CreateLayer("1", srs=osr.SpatialReference(wkt=proj))
    fd = ogr.FieldDefn("code", ogr.OFTInteger)
    dst_layer.CreateField(fd)

    gdal.Polygonize(outband, mask_band, dst_layer, 0)
    shp_ds.Release()


def raster2shp_mem(shp_path, array, geo_trans, proj, nd_value, dtype):


    gtiffDriver = gdal.GetDriverByName("MEM")
    outDataSet = gtiffDriver.Create("data", array.shape[1], array.shape[0], 1, dtype)
    outDataSet.SetGeoTransform(geo_trans)
    outDataSet.SetProjection(proj)
    outband = outDataSet.GetRasterBand(1)
    outband.WriteArray(array, 0, 0)
    outband.SetNoDataValue(nd_value)
    mask_band = outband.GetMaskBand()

    drv = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = drv.CreateDataSource(shp_path)
    dst_layer = shp_ds.CreateLayer("data", srs=osr.SpatialReference(wkt=proj))
    fd = ogr.FieldDefn("code", ogr.OFTInteger)
    dst_layer.CreateField(fd)

    gdal.Polygonize(outband, mask_band, dst_layer, 0)
    shp_ds.Destroy()


def raster2vector_mem(array, geo_trans, proj, nd_value, dtype):

    mem_raster_driver = gdal.GetDriverByName("MEM")
    memDataSet = mem_raster_driver.Create("temp", array.shape[1], array.shape[0], 1, dtype)
    memDataSet.SetGeoTransform(geo_trans)
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


def cor2idx(lon, lat, gt):
    return math.floor((lat-gt[3])/gt[5]), math.floor((lon-gt[0])/gt[1])


def cor2idx_list(cor_list, geotrans):
    return [cor2idx(lon, lat, geotrans) for lon,lat in cor_list]


def get_mainland_samples(shp_fn, geo_trans):

    ds = ogr.Open(shp_fn)
    layer = ds.GetLayer()
    geom_type = layer.GetGeomType()
    if geom_type != 1:
        raise RuntimeError("The geometry type of coastline samples must be point!")

    def get_point(pFeature):
        geom = pFeature.GetGeometryRef()
        return geom.GetX(), geom.GetY()

    corList = [get_point(feature) for feature in layer]
    idxList = cor2idx_list(corList, geo_trans)
    return idxList


def get_raster_value_by_loc(tif_path, cidx, ridx):
    if not os.path.exists(tif_path):
        raise IOError("Input tif file %s not found!" % tif_path)

    ds = gdal.Open(tif_path)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray(cidx, ridx, 1, 1)
    return arr[0, 0]


def get_raster_value_by_coor(tif_path, lon, lat):
    if not os.path.exists(tif_path):
        raise IOError("Input tif file %s not found!" % tif_path)

    ds = gdal.Open(tif_path)
    geo_trans = ds.GetGeoTransform()
    band = ds.GetRasterBand(1)
    ridx, cidx = cor2idx(lon, lat, geo_trans)
    arr = band.ReadAsArray(cidx, ridx, 1, 1)
    return arr[0, 0]


def get_raster_arr_by_loc(tif_path, x, y, x_buff, y_buff):
    if not os.path.exists(tif_path):
        raise IOError("Input tif file %s not found!" % tif_path)

    ds = gdal.Open(tif_path)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray(x, y, x_buff, y_buff)
    return arr


def get_raster_geotransform(tif_path):
    if not os.path.exists(tif_path):
        raise IOError("Input tif file %s not found!" % tif_path)

    ds = gdal.Open(tif_path)
    geo_trans = ds.GetGeoTransform()
    return geo_trans


def get_raster_extent(tif_path):

    if not os.path.exists(tif_path):
        raise IOError("Input tif file %s not found!" % tif_path)

    ds = gdal.Open(tif_path)
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    geo_trans = ds.GetGeoTransform()
    proj = ds.GetProjection()
    return rows, cols, geo_trans, proj
