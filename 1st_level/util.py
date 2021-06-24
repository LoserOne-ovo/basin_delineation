from osgeo import gdal
import numpy as np


class ReadTif:

    def __init__(self, tif_path):
        """
        使用类读取tif文件，减少代码冗余
        :param tif_path: tif文件路径
        """

        ds = gdal.Open(tif_path)
        if ds is None:
            print('No such .tif file exists!')
        else:
            self.cols = ds.RasterXSize
            self.rows = ds.RasterYSize
            self.geotransform = ds.GetGeoTransform()
            self.originX = self.geotransform[0]
            self.originY = self.geotransform[3]
            self.pixelWidth = self.geotransform[1]
            self.pixelHeight = self.geotransform[5]
            self.proj = ds.GetProjection()
            band = ds.GetRasterBand(1)
            self.data = band.ReadAsArray(0, 0, self.cols, self.rows)
            # 内存回收
            del band, ds


    @classmethod
    def array2tif(cls, out_path, array, geotransform, proj, nd_value, dtype=gdal.GDT_Int16, opt=None):

        gtiffDriver = gdal.GetDriverByName('GTiff')

        if gtiffDriver is None:
            raise ValueError("Can't find GeoTiff Driver")
        if opt is None:
            outDataSet = gtiffDriver.Create(out_path, array.shape[1], array.shape[0], 1, dtype)
        else:
            outDataSet = gtiffDriver.Create(out_path, array.shape[1], array.shape[0], 1, dtype, opt)
        outDataSet.SetGeoTransform(geotransform)
        outDataSet.SetProjection(proj)
        outband = outDataSet.GetRasterBand(1)
        outband.WriteArray(array, 0, 0)
        outband.SetNoDataValue(nd_value)
        outband.FlushCache()


class Array2D:

    @staticmethod
    def binarization(source, front, background=0):

        if isinstance(source, np.ndarray):
            if background == 0:
                res = np.zeros(source.shape, dtype=np.uint8)
                if isinstance(front, list):
                    uniq_front = ListOperation.unique(front)
                    for i in range(len(uniq_front)):
                        res[source == uniq_front[i]] = 1
                    return res
                else:
                    raise TypeError("the parameter 'front' of <binarizaion> must be in the type of list!")

            elif background == 1:
                res = np.ones(source.shape, dtype=np.uint8)
                if isinstance(front, list):
                    uniq_front = ListOperation.unique(front)
                    for i in range(len(uniq_front)):
                        res[source == uniq_front[i]] = 0
                    return res
                else:
                    raise TypeError("the parameter 'front' of <binarizaion> must be in the type of list!")
            else:
                raise ValueError("the parameter 'background' of <binarization> must be 0 or 1!")
        else:
            raise TypeError("the parameter 'ndarray' of <binarizaion> must be in the type of numpy.ndarray!")


class ListOperation:

    @staticmethod
    def unique(origin_list):

        res = []
        for i in range(len(origin_list)):
            if i == origin_list.index(origin_list[i]):
                res.append(origin_list[i])
        return res
