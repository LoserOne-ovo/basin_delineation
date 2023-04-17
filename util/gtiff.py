import os
from osgeo import gdal


DT_Byte = gdal.GDT_Byte
DT_U16 = gdal.GDT_UInt16
DT_I16 = gdal.GDT_Int16
DT_U32 = gdal.GDT_UInt32
DT_I32 = gdal.GDT_Int32
DT_F32 = gdal.GDT_Float32
DT_F64 = gdal.GDT_Float64


class GTiffDataSet:

    Driver = None
    Data = None
    NoDataValue = None
    DataType = 0
    rows = 0
    cols = 0
    GeoTransform = None
    Projection = None

    def __init__(self, path=None):
        self.register()
        if path is not None:
            self.read_file(path)

    def read_file(self, tif_path):
        if not os.path.exists(tif_path):
            raise IOError("Input tif file %s not found!" % tif_path)

        ds = gdal.Open(tif_path)
        self.GeoTransform = ds.GetGeoTransform()
        self.Projection = ds.GetProjection()
        band = ds.GetRasterBand(1)
        self.rows = band.YSize
        self.cols = band.XSize
        self.Data = band.ReadAsArray()
        self.NoDataValue = band.GetNoDataValue()
        self.DataType = band.DataType
        del band, ds

    def register(self):
        self.Driver = gdal.GetDriverByName("GTiff")
        if self.Driver is None:
            raise ValueError("Can't find GeoTiff Driver")

    def write2disk(self, out_path, create_option=None):
        if create_option is None:
            create_option = []
        if self.check_status() is False:
            raise RuntimeError("Can't output GeoTiff dataset!")
        ds = self.Driver.Create(out_path, self.cols, self.rows, 1, self.DataType, create_option)
        ds.SetGeoTransform(self.GeoTransform)
        ds.SetProjection(self.Projection)
        band = ds.GetRasterBand(1)
        band.WriteArray(self.Data, 0, 0)
        if self.NoDataValue is not None:
            band.SetNoDataValue(self.NoDataValue)
        band.FlushCache()
        del band, ds

    def check_status(self):
        if self.Driver is None:
            print("GeoTiff Driver is not registered!")
            return False
        if self.Data is None:
            print("Missing output data!")
            return False
        if self.rows <= 0 or self.cols <= 0:
            print("Shape of output data is less than (1, 1)!")
            return False
        if self.DataType not in range(1, 8):
            print("Unsupported Datatype!")
            return False
        if self.GeoTransform is None:
            print("GeoTiff dataset Missing GeoTransform information!")
            return False
        if self.Projection is None:
            print("GeoTiff dataset Missing Projection information!")
            return False

    def copy(self, copy_data=False):

        ds = GTiffDataSet()
        ds.rows = self.rows
        ds.cols = self.cols
        ds.GeoTransform = self.GeoTransform
        ds.Projection = self.Projection
        if copy_data is True:
            ds.Data = self.Data.copy()
            ds.DataType = self.DataType
            ds.NoDataValue = self.NoDataValue

        return ds

