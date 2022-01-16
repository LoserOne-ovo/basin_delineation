import os
import sys
sys.path.append("..")
import numpy as np
from osgeo import ogr, osr, gdal
from file_op import get_basin_folder
from db_op import get_ul_offset, get_sub_basin_info, update_many_alter_status
from util.raster import read_single_tif, read_tif_files, mask_whole_basin_int32, raster2vector_mem
from interface import *


def main_lake_per_task(basin_code, lake_list, river_ths, level, lake_folder, basin_root, alter_db, upd_sql, basin_stat_db, out_folder):
    """

    :param basin_code:
    :param lake_list:
    :param river_ths:
    :param level:
    :param lake_folder:
    :param basin_root:
    :param basin_stat_db:
    :param out_folder:
    :return:
    """

    max_lake_id = max(lake_list)
    basin_folder = get_basin_folder(basin_root, basin_code)

    # 先将湖泊shp栅格化
    lake_arr, geo_trans, proj = build_lake_arr(basin_code, lake_list, basin_folder, lake_folder)
    # 追踪湖泊的坡面
    paint_lake_slope(lake_arr, max_lake_id, basin_code, basin_folder, river_ths)

    # 重组湖泊和流域的shp
    if len(basin_code) == level:
        upd_val = rebuild_shp_same_level(lake_arr, geo_trans, proj, basin_code, lake_list, max_lake_id, out_folder)
    else:
        upd_val = rebuild_shp_high_level(lake_arr, geo_trans, proj, basin_code, lake_list, max_lake_id, out_folder,
                                         level, basin_folder, basin_stat_db, basin_root)
    # 更新流域替换信息
    update_many_alter_status(alter_db, upd_sql, upd_val)

    return 1


def build_lake_arr(basin_code, lake_list, folder, lake_folder):
    """
    矢量栅格化湖泊shp
    :param basin_code:
    :param lake_list:
    :param folder:
    :param lake_folder:
    :return:
    """

    lake_num = len(lake_list)
    # 读取流域范围
    dir_tif = os.path.join(folder, basin_code + "_dir.tif")
    basin_arr, geo_trans, proj = mask_whole_basin_int32(dir_tif)
    rows, cols = basin_arr.shape

    # 创建Rasterize的目标栅格集
    mem_grid_driver = gdal.GetDriverByName("MEM")
    grid_ds = mem_grid_driver.Create(basin_code + "_lak.tif", cols, rows, 1, gdal.GDT_Int32)
    grid_ds.SetGeoTransform(geo_trans)
    grid_ds.SetProjection(proj)
    outband = grid_ds.GetRasterBand(1)
    outband.WriteArray(basin_arr.astype(np.int32), 0, 0)

    # 如果只有一个湖泊，直接用源湖泊shp做Rasterize
    if lake_num == 1:
        lake_shp = os.path.join(lake_folder, "%d.shp" % lake_list[0])
        lake_ds = ogr.Open(lake_shp)
        layer = lake_ds.GetLayer()
        gdal.RasterizeLayer(grid_ds, [1], layer, options=["ATTRIBUTE=Hylak_id"])
        lake_arr = grid_ds.ReadAsArray()
        lake_ds.Destroy()

    # 如果有多个湖泊，则在内存中创建一个新的shp
    else:
        lake_shp = os.path.join(lake_folder, "%d.shp" % lake_list[0])
        single_lake_ds = ogr.Open(lake_shp)
        single_lake_layer = single_lake_ds.GetLayer()
        srs = single_lake_layer.GetSpatialRef()

        mem_vector_driver = ogr.GetDriverByName("MEMORY")
        lake_ds = mem_vector_driver.CreateDataSource(basin_code + "_lake")
        layer = lake_ds.CopyLayer(single_lake_layer, "lakes")
        single_lake_ds.Destroy()

        for i in range(1, lake_num):
            lake_shp = os.path.join(lake_folder, "%d.shp" % lake_list[i])
            single_lake_ds = ogr.Open(lake_shp)
            single_lake_layer = single_lake_ds.GetLayer()
            for feature in single_lake_layer:
                layer.CreateFeature(feature)
            single_lake_ds.Destroy()

        gdal.RasterizeLayer(grid_ds, [1], layer, options=["ATTRIBUTE=Hylak_id"])
        lake_arr = grid_ds.ReadAsArray()
        lake_ds.Destroy()

    return lake_arr, geo_trans, proj


def paint_lake_slope(lake_arr, max_lake_id, code, folder, river_threshold):
    """

    :param lake_arr:
    :param max_lake_id:
    :param code:
    :param folder:
    :param river_threshold:
    :return:
    """
    # 读取流域栅格数据
    dir_arr, upa_arr, elv_arr, geo_trans, proj = read_tif_files(folder, code, 0)
    # 计算逆流向
    re_dir_arr = calc_reverse_dir(dir_arr)
    # 修正湖泊河网
    correct_lake_network_int32_c(lake_arr, dir_arr, re_dir_arr, upa_arr, river_threshold)
    # 绘制湖泊坡面
    # paint_lake_hillslope_int32_c(lake_arr, max_lake_id, re_dir_arr, upa_arr, river_threshold)
    paint_lake_hillslope_2_int32_c(lake_arr, max_lake_id, dir_arr, re_dir_arr, upa_arr, river_threshold)

    # 保存栅格文件
    # out_folder = r""
    # out_tif = os.path.join(out_folder, basin_code + "_lak.tif")
    # array2tif(out_tif, lake_arr, geo_trans, proj, nd_value=-9999, dtype=5)

    return 1


def rebuild_shp_same_level(lake_arr, geo_trans, proj, basin_code, lake_list, max_lake_id, out_folder):
    """

    :param lake_arr:
    :param geo_trans:
    :param proj:
    :param basin_code:
    :param lake_list:
    :param max_lake_id:
    :param out_folder:
    :return:
    """

    upd_status = 2
    if lake_arr.__contains__(0):
        basin_arr = lake_arr.copy()
        basin_arr[basin_arr != 0] = -9999
        build_basin_shp(basin_arr, basin_code, geo_trans, proj, out_folder)
        upd_status = 1

    lake_arr[lake_arr == 0] = -9999
    build_lake_shp(lake_arr, basin_code, lake_list, max_lake_id, geo_trans, proj, out_folder)

    return [(upd_status, basin_code)]


def rebuild_shp_high_level(lake_arr, geo_trans, proj, basin_code, lake_list, max_lake_id,
                           out_folder, level, basin_folder, stat_db_path, root_folder):
    """

    :param lake_arr:
    :param geo_trans:
    :param proj:
    :param basin_code:
    :param lake_list:
    :param max_lake_id:
    :param out_folder:
    :param level:
    :param stat_db_path:
    :param root_folder:
    :return:
    """
    # 查询流域的offset
    basin_db = os.path.join(basin_folder, basin_code + ".db")
    offset = get_ul_offset(basin_db)

    # 在数据中库中所有的次级流域
    sub_basin_list = get_sub_basin_info(stat_db_path, basin_code, level)

    ################################
    #   循环每一个子流域，重构流域shp   #
    ################################

    upd_val = []
    for record in sub_basin_list:

        sub_basin_code = record[0]
        sub_basin_folder = get_basin_folder(root_folder, sub_basin_code)
        sub_basin_db = os.path.join(sub_basin_folder, sub_basin_code + ".db")
        sub_basin_offset = get_ul_offset(sub_basin_db)

        # 读取左上角offset
        ref_y = sub_basin_offset[0] - offset[0]
        ref_x = sub_basin_offset[1] - offset[1]

        # 读取子流域范围
        sub_basin_dir = os.path.join(sub_basin_folder, sub_basin_code + "_dir.tif")
        sub_dir_arr, sub_geo_trans, sub_proj = read_single_tif(sub_basin_dir)
        sub_rows, sub_cols = sub_dir_arr.shape
        sub_basin_arr = lake_arr[ref_y: ref_y + sub_rows, ref_x: ref_x + sub_cols].copy()
        sub_mask = sub_dir_arr != 247
        sub_basin_arr[~sub_mask] = -9999

        """
            判断在流域范围内是否有0值像元：
            --有：对该流域去除湖泊和坡面的部分进行矢量化
            --无：舍去该流域
        """

        total_num = np.sum(sub_mask)
        zero_num = np.sum(sub_basin_arr == 0)
        # 判断子流域范围内有没有湖泊和坡面
        if 0 < zero_num < total_num:
            # 去除湖泊、湖泊坡面的部分, 然后矢量化
            sub_basin_arr[sub_basin_arr != 0] = -9999
            build_basin_shp(sub_basin_arr, sub_basin_code, sub_geo_trans, sub_proj, out_folder)
            upd_val.append((1, sub_basin_code))
        elif zero_num == 0:
            upd_val.append((2, sub_basin_code))
        else:
            pass

    ##########################
    #   重构湖泊和湖泊坡面shp   #
    ##########################

    lake_arr[lake_arr == 0] = -9999
    build_lake_shp(lake_arr, basin_code, lake_list, max_lake_id, geo_trans, proj, out_folder)

    return upd_val


def build_lake_shp(lake_arr, basin_code, lake_list, max_lake_id, geo_trans, proj, out_folder):

    shp_driver = ogr.GetDriverByName("ESRI Shapefile")
    srs = osr.SpatialReference(wkt=proj)

    # 提取湖泊和湖泊坡面
    lake_shp = os.path.join(out_folder, basin_code + "_lak_alt.shp")
    lake_ds = shp_driver.CreateDataSource(lake_shp)
    lake_layer = lake_ds.CreateLayer("lake", srs=srs, geom_type=ogr.wkbMultiPolygon)
    pidFieldDefn = ogr.FieldDefn("PFAF_ID", ogr.OFTString)
    pidFieldDefn.SetWidth(15)
    lake_layer.CreateField(pidFieldDefn)
    typeFieldDefn = ogr.FieldDefn("TYPE", ogr.OFTInteger)
    lake_layer.CreateField(typeFieldDefn)
    lidFieldDefn = ogr.FieldDefn("LAKE_ID", ogr.OFTInteger)
    lake_layer.CreateField(lidFieldDefn)
    featureDefn = lake_layer.GetLayerDefn()

    temp_ds = raster2vector_mem(lake_arr, geo_trans, proj, nd_value=-9999, dtype=5)
    src_layer = temp_ds.GetLayer()

    # 循环提取每一个湖泊
    for lake_id in lake_list:
        # 先提取湖泊
        src_layer.SetAttributeFilter("code=%d" % lake_id)
        lake_geometry = ogr.Geometry(ogr.wkbMultiPolygon)
        for feature in src_layer:
            geom = feature.GetGeometryRef()
            geom_type = geom.GetGeometryType()
            if geom_type == 6:
                for sub_geom in geom:
                    lake_geometry.AddGeometry(sub_geom)
            elif geom_type == 3:
                lake_geometry.AddGeometry(geom)
            else:
                raise RuntimeError("Unsupported Geometry Type %d!" % geom_type)

        lake_feature = ogr.Feature(featureDefn)
        lake_feature.SetGeometry(lake_geometry)
        lake_feature.SetField("PFAF_ID", basin_code)
        lake_feature.SetField("TYPE", 2)
        lake_feature.SetField("LAKE_ID", lake_id)
        lake_layer.CreateFeature(lake_feature)

        # 再提取对应的坡面
        src_layer.SetAttributeFilter("code=%d" % (lake_id + max_lake_id))
        lake_slope_geometry = ogr.Geometry(ogr.wkbMultiPolygon)
        for feature in src_layer:
            geom = feature.GetGeometryRef()
            geom_type = geom.GetGeometryType()
            if geom_type == 6:
                for sub_geom in geom:
                    lake_slope_geometry.AddGeometry(sub_geom)
            elif geom_type == 3:
                lake_slope_geometry.AddGeometry(geom)
            else:
                raise RuntimeError("Unsupported Geometry Type %d!" % geom_type)

        lake_slope_feature = ogr.Feature(featureDefn)
        lake_slope_feature.SetGeometry(lake_slope_geometry)
        lake_slope_feature.SetField("PFAF_ID", basin_code)
        lake_slope_feature.SetField("TYPE", 3)
        lake_slope_feature.SetField("LAKE_ID", lake_id)
        lake_layer.CreateFeature(lake_slope_feature)

    lake_layer.SyncToDisk()
    lake_ds.Destroy()
    temp_ds.Destroy()


def build_basin_shp(basin_arr, basin_code, geo_trans, proj, out_folder):
    """

    :param basin_arr:
    :param basin_code:
    :param geo_trans:
    :param proj:
    :param out_folder:
    :return:
    """

    shp_driver = ogr.GetDriverByName("ESRI Shapefile")
    srs = osr.SpatialReference(wkt=proj)

    # 先创建输出对象
    basin_shp = os.path.join(out_folder, basin_code + "_bas_alt.shp")
    basin_ds = shp_driver.CreateDataSource(basin_shp)
    basin_layer = basin_ds.CreateLayer("basin", srs=srs, geom_type=ogr.wkbMultiPolygon)
    pidFieldDefn = ogr.FieldDefn("PFAF_ID", ogr.OFTString)
    pidFieldDefn.SetWidth(15)
    basin_layer.CreateField(pidFieldDefn)
    typeFieldDefn = ogr.FieldDefn("TYPE", ogr.OFTInteger)
    basin_layer.CreateField(typeFieldDefn)
    lidFieldDefn = ogr.FieldDefn("LAKE_ID", ogr.OFTInteger)
    basin_layer.CreateField(lidFieldDefn)
    featureDefn = basin_layer.GetLayerDefn()

    temp_ds = raster2vector_mem(basin_arr, geo_trans, proj, nd_value=-9999, dtype=5)
    src_layer = temp_ds.GetLayer()

    basin_geometry = ogr.Geometry(ogr.wkbMultiPolygon)
    for feature in src_layer:
        geom = feature.GetGeometryRef()
        geom_type = geom.GetGeometryType()
        if geom_type == 6:
            for sub_geom in geom:
                basin_geometry.AddGeometry(sub_geom)
        elif geom_type == 3:
            basin_geometry.AddGeometry(geom)
        else:
            raise RuntimeError("Unsupported Geometry Type %d!" % geom_type)

    basin_feature = ogr.Feature(featureDefn)
    basin_feature.SetGeometry(basin_geometry)
    basin_feature.SetField("PFAF_ID", basin_code)
    basin_feature.SetField("TYPE", 1)
    basin_feature.SetField("LAKE_ID", -9999)
    basin_layer.CreateFeature(basin_feature)

    basin_layer.SyncToDisk()
    basin_ds.Destroy()
    temp_ds.Destroy()
