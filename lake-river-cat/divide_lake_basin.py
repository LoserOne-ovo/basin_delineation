import os
import sys
sys.path.append(r"../")
import numpy as np
import db_op as dp
from osgeo import ogr, gdal, osr
from util import raster
from util import interface as cfunc
from multiprocessing import Pool
from numba import jit
from functools import partial


@jit(nopython=True)
def get_downstream_index(i, j, direction):
    if direction == 1:
        return i, j + 1
    if direction == 2:
        return i + 1, j + 1
    if direction == 4:
        return i + 1, j
    if direction == 8:
        return i + 1, j - 1
    if direction == 16:
        return i, j - 1
    if direction == 32:
        return i - 1, j - 1
    if direction == 64:
        return i - 1, j
    if direction == 128:
        return i - 1, j + 1

    return -1, -1


class DealWithLake:

    @staticmethod
    def filter_lake(lake_shp, area_threshold):
        lakeDict = {}
        lake_num = 0
        # 挑选面积大于阈值的湖泊
        ds = ogr.Open(lake_shp)
        layer = ds.GetLayer()

        for feature in layer:
            area = feature.GetField("Lake_area")
            if area > area_threshold:
                fid = feature.GetFID()
                hylake_id = feature.GetField("Hylak_id")
                lakeDict[fid] = (hylake_id, area)
                lake_num += 1

        ds.Destroy()
        return lakeDict, lake_num

    @staticmethod
    def build_lake_arr(lakeFIDs, lake_shp, rows, cols, geo_trans, proj):
        # mapDict = {}
        lake_value = 0
        burn_field_name = "value"
        # 创建Rasterize的目标栅格集
        mem_grid_driver = gdal.GetDriverByName("MEM")
        grid_ds = mem_grid_driver.Create("lake_tif", cols, rows, 1, gdal.GDT_Int32)
        grid_ds.SetGeoTransform(geo_trans)
        grid_ds.SetProjection(proj)
        outband = grid_ds.GetRasterBand(1)
        basin_arr = np.zeros((rows, cols), dtype=np.int32)
        outband.WriteArray(basin_arr.astype(np.int32), 0, 0)

        # 读取湖泊矢量数据
        lake_shp_ds = ogr.Open(lake_shp)
        lake_layer = lake_shp_ds.GetLayer()
        srs = lake_layer.GetSpatialRef()

        # 创建新的shp
        mem_vector_driver = ogr.GetDriverByName("MEMORY")
        mem_shp_ds = mem_vector_driver.CreateDataSource("lake_shp")
        mem_layer = mem_shp_ds.CreateLayer("data", srs=srs, geom_type=ogr.wkbPolygon)
        burnValueField = ogr.FieldDefn(burn_field_name, ogr.OFTInteger)
        mem_layer.CreateField(burnValueField)
        mem_featureDefn = mem_layer.GetLayerDefn()

        # 挑选湖泊
        for fid in lakeFIDs:
            feature = lake_layer.GetFeature(fid)
            # hylake_id = feature.GetField("Hylak_id")
            lake_value += 1
            mem_feature = ogr.Feature(mem_featureDefn)
            mem_feature.SetField(burn_field_name, lake_value)
            mem_feature.SetGeometry(feature.GetGeometryRef())
            mem_layer.CreateFeature(mem_feature)
            # mapDict[lake_value] = hylake_id

        gdal.RasterizeLayer(grid_ds, [1], mem_layer, options=["ATTRIBUTE=%s" % burn_field_name])
        lake_arr = outband.ReadAsArray()

        lake_shp_ds.Destroy()
        mem_shp_ds.Destroy()
        return lake_arr

    @staticmethod
    def build_lake_shp(lake_arr, lake_num, lakeIDList, envelopes, geo_trans, proj, temp_folder):
        shp_driver = ogr.GetDriverByName("ESRI Shapefile")
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        ul_lon, width, _, ul_lat, _, height = geo_trans
        for i in range(lake_num):
            lake_id = lakeIDList[i]
            # 湖泊及其坡面存在同一个shapefile中
            out_shp = os.path.join(temp_folder, "%d.shp" % lake_id)
            ds = shp_driver.CreateDataSource(out_shp)
            layer = ds.CreateLayer("data", srs=srs, geom_type=ogr.wkbMultiPolygon)
            # 定义属性字段
            lidFieldDefn = ogr.FieldDefn("LAKE_ID", ogr.OFTInteger)
            layer.CreateField(lidFieldDefn)
            typeFieldDefn = ogr.FieldDefn("TYPE", ogr.OFTInteger)
            layer.CreateField(typeFieldDefn)
            featureDefn = layer.GetLayerDefn()
            # 提取湖泊范围
            hs_value = i + 1
            min_row, min_col, max_row, max_col = envelopes[hs_value]
            sub_basin_arr = np.zeros((max_row - min_row + 1, max_col - min_col + 1), dtype=np.uint8)
            mask_arr = lake_arr[min_row:max_row + 1, min_col:max_col + 1]
            sub_basin_arr[mask_arr == hs_value] = 1
            # 计算新的GeoTransform
            sub_geo_trans = (ul_lon + min_col * width, width, 0.0, ul_lat + min_row * height, 0.0, height)
            # 矢量化，合并成一个multipolygon
            geom = DealWithBasin.polygonize_basin(sub_basin_arr, sub_geo_trans, proj, nd_value=0, dtype=gdal.GDT_Byte)
            # 添加湖泊矢量
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(geom)
            feature.SetField("LAKE_ID", lake_id)
            feature.SetField("TYPE", 1)
            layer.CreateFeature(feature)

            # 湖泊坡面矢量
            hs_value = i + 1 + lake_num
            min_row, min_col, max_row, max_col = envelopes[hs_value]
            sub_basin_arr = np.zeros((max_row - min_row + 1, max_col - min_col + 1), dtype=np.uint8)
            mask_arr = lake_arr[min_row:max_row + 1, min_col:max_col + 1]
            sub_basin_arr[mask_arr == hs_value] = 1
            # 计算新的GeoTransform
            sub_geo_trans = (ul_lon + min_col * width, width, 0.0, ul_lat + min_row * height, 0.0, height)
            # 矢量化，合并成一个multipolygon
            geom = DealWithBasin.polygonize_basin(sub_basin_arr, sub_geo_trans, proj, nd_value=0, dtype=gdal.GDT_Byte)
            # 添加湖泊矢量
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(geom)
            feature.SetField("LAKE_ID", lake_id)
            feature.SetField("TYPE", 2)
            layer.CreateFeature(feature)

            # 释放内存
            layer.SyncToDisk()
            ds.Destroy()


class DealWithBasin:

    @staticmethod
    def polygonize_basin(array, geotransform, proj, nd_value, dtype):
        mem_raster_driver = gdal.GetDriverByName("MEM")
        memDataSet = mem_raster_driver.Create("tempR", array.shape[1], array.shape[0], 1, dtype)
        memDataSet.SetGeoTransform(geotransform)
        memDataSet.SetProjection(proj)
        outband = memDataSet.GetRasterBand(1)
        outband.WriteArray(array, 0, 0)
        outband.SetNoDataValue(nd_value)
        mask_band = outband.GetMaskBand()

        mem_vector_dirver = ogr.GetDriverByName("MEMORY")
        mem_vector_ds = mem_vector_dirver.CreateDataSource("tempS")
        dst_layer = mem_vector_ds.CreateLayer("data", srs=osr.SpatialReference(wkt=proj))
        fd = ogr.FieldDefn("code", ogr.OFTInteger)
        dst_layer.CreateField(fd)

        gdal.Polygonize(outband, mask_band, dst_layer, 0)

        fNum = dst_layer.GetFeatureCount()
        if fNum == 1:
            feature = dst_layer.GetFeature(0)
            geom = feature.GetGeometryRef()
            basin_geom = ogr.ForceToMultiPolygon(geom)
        else:
            basin_geom = ogr.Geometry(ogr.wkbMultiPolygon)
            for feature in dst_layer:
                geom = feature.GetGeometryRef()
                basin_geom.AddGeometry(geom)
            basin_geom = basin_geom.UnionCascaded()
        mem_vector_ds.Destroy()

        return basin_geom

    @staticmethod
    def build_new_basin_shp(sub_arr, extractValues, geo_trans, proj, out_path):
        shp_driver = ogr.GetDriverByName("ESRI Shapefile")
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        ds = shp_driver.CreateDataSource(out_path)
        layer = ds.CreateLayer("data", srs=srs, geom_type=ogr.wkbMultiPolygon)
        # 定义属性字段
        lidFieldDefn = ogr.FieldDefn("BASIN_ID", ogr.OFTInteger)
        layer.CreateField(lidFieldDefn)
        featureDefn = layer.GetLayerDefn()

        extract_arr = np.zeros(sub_arr.shape, dtype=np.uint8)
        for probe, extract_value in enumerate(extractValues):
            extract_arr[:, :] = 0
            extract_arr[sub_arr == extract_value] = 1
            # 矢量化
            geom = DealWithBasin.polygonize_basin(extract_arr, geo_trans, proj, nd_value=0, dtype=gdal.GDT_Byte)
            # 添加湖泊矢量
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(geom)
            feature.SetField("BASIN_ID", int(extract_value))
            layer.CreateFeature(feature)

        # 释放内存
        layer.SyncToDisk()
        ds.Destroy()

    @staticmethod
    def deal_with_single_basin(subBasinInfo, lake_tif, lake_num, bench_offset, root, temp_folder):
        src_code, code, down_code, btype, outlet_lon, outlet_lat, inlet_lon, inlet_lat = subBasinInfo
        str_src_code = str(src_code)
        src_folder = os.path.join(root, *str_src_code)
        src_tif = os.path.join(src_folder, str_src_code + ".tif")
        src_db = os.path.join(src_folder, str_src_code + '.db')

        # 读取子流域栅格数据
        sub_basin_mask, sub_trans, proj = raster.read_single_tif(src_tif)
        # 读取子流域位置信息
        ul_offset = dp.get_ul_offset(src_db)
        # 确定子流域在当前流域中的范围
        min_row = ul_offset[0] - bench_offset[0]
        min_col = ul_offset[1] - bench_offset[1]
        sub_rows, sub_cols = ul_offset[2:4]
        # 去除子流域外的信息
        sub_basin_arr = raster.get_raster_arr_by_loc(lake_tif, min_col, min_row, sub_cols, sub_rows)
        sub_basin_arr[sub_basin_mask == 0] = -1

        unique_values = np.unique(sub_basin_arr)
        zero_flag = 0
        upstreamList = []
        upstream_num = 0
        hs_num = 0
        start_BasinID = 2 * lake_num

        # 分析子流域的组成
        for u_value in unique_values:
            if u_value == 0:
                zero_flag = 1
            elif u_value > start_BasinID:
                upstreamList.append(u_value)
                upstream_num += 1
            elif 0 < u_value <= start_BasinID:
                hs_num += 1
            else:
                continue

        result = []
        head_water_code = None
        down_sub_code = None
        down_lake = -1

        # 如果该流域完全被湖泊及其坡面覆盖
        if upstream_num == 0 and zero_flag == 0:
            pass

        # 如果该流域被分割成单个子流域
        elif (zero_flag + upstream_num) == 1:
            sub_code = 0 if zero_flag == 1 else int(upstreamList[0])
            if hs_num == 0:
                u_status = 0
                head_water_code = sub_code
            else:
                u_status = 1
                out_shp = os.path.join(temp_folder, "%d.shp" % code)
                DealWithBasin.build_new_basin_shp(sub_basin_arr, [sub_code], sub_trans, proj, out_shp)
                if btype == 2:
                    inlet_value = int(raster.get_raster_value_by_coor(lake_tif, inlet_lon, inlet_lat))
                    if inlet_value == 0 or inlet_value > start_BasinID:
                        head_water_code = inlet_value

            record = (code, sub_code, down_code, down_sub_code, down_lake, btype,
                      outlet_lon, outlet_lat, u_status, src_code)
            result.append(record)

        # 如果该流域被分割成多个子流域
        else:
            extract_values = upstreamList.copy()
            if zero_flag == 1:
                extract_values.append(0)
            out_shp = os.path.join(temp_folder, "%d.shp" % code)
            DealWithBasin.build_new_basin_shp(sub_basin_arr, extract_values, sub_trans, proj, out_shp)
            for extract_value in extract_values:
                u_status = 2
                sub_code = int(extract_value)
                record = (code, sub_code, down_code, down_sub_code, down_lake, btype,
                          outlet_lon, outlet_lat, u_status, src_code)
                result.append(record)
            if btype == 2:
                inlet_value = int(raster.get_raster_value_by_coor(lake_tif, inlet_lon, inlet_lat))
                if inlet_value == 0 or inlet_value > lake_num:
                    head_water_code = inlet_value

        result.append((head_water_code, len(upstreamList)))
        return result


def workflow_lake(lakeDict, lake_num, lake_shp, basin_tif, mask_tif, mask_offset, root,
                  ths, min_river_ths, lake_tif, lake_out_folder):
    """
    1. 栅格化湖泊
    2. 生成湖泊shapefile
    :return:
    """

    # 读取当前流域的流向，汇流累积量和高程数据
    dir_arr, upa_arr, elv_arr, geo_trans, proj = raster.read_tif_files(root, 0, mask_tif, mask_offset)
    rows, cols = dir_arr.shape

    # 获取湖泊的fid
    lakeFIDs = list(lakeDict.keys())

    # 栅格化湖泊矢量
    lake_arr = DealWithLake.build_lake_arr(lakeFIDs, lake_shp, rows, cols, geo_trans, proj)
    # 计算逆流向
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    # 修正湖泊河网
    cfunc.correct_lake_network_int32_c(lake_arr, dir_arr, re_dir_arr, upa_arr, min_river_ths)
    # 追踪湖泊坡面和上游
    outlets, basin_num = cfunc.paint_lake_hillslope_new_int32_c(lake_arr, lake_num, dir_arr, re_dir_arr, upa_arr,
                                                                ths)
    # 计算各流域的范围
    rows, cols = lake_arr.shape
    up_basin_num = basin_num - lake_num
    envelopes = np.zeros((2 * lake_num + up_basin_num + 1, 4), dtype=np.int32)
    envelopes[:, 0] = rows
    envelopes[:, 1] = cols
    cfunc.get_basin_envelopes_int32(lake_arr, envelopes)

    # 生成湖泊和湖泊坡面矢量
    DealWithLake.build_lake_shp(lake_arr, lake_num, lakeFIDs, envelopes, geo_trans, proj, lake_out_folder)
    ul_lon, width, _, ul_lat, _, height = geo_trans

    lakeRecords = []
    # 计算湖泊的下游流域
    for i in range(1, lake_num + 1):
        fid = lakeFIDs[i - 1]
        lake_id = lakeDict[fid][0]
        # 计算湖泊的下游
        outlet_ridx, outlet_cidx = outlets[i]
        outlet_lon = ul_lon + (outlet_cidx + 0.5) * width
        outlet_lat = ul_lat + (outlet_ridx + 0.5) * height
        # 判断是否是内流湖泊
        if dir_arr[outlet_ridx, outlet_cidx] == 255:
            btype = 3
            down_code = -1
            down_sub_code = None
        # 判断是否流入海洋
        elif dir_arr[outlet_ridx, outlet_cidx] == 0:
            btype = 2
            down_code = 0
            down_sub_code = None
        # 流入下游流域
        else:
            btype = 2
            down_ridx, down_cidx = get_downstream_index(outlet_ridx, outlet_cidx, dir_arr[outlet_ridx, outlet_cidx])
            src_down_ridx = mask_offset[0] + down_ridx
            src_down_cidx = mask_offset[1] + down_cidx
            down_code = int(raster.get_raster_value_by_loc(basin_tif, src_down_cidx, src_down_ridx))
            down_sub_code = int(lake_arr[down_ridx, down_cidx])

        lakeRecords.append((fid, lake_id, down_code, down_sub_code, btype, outlet_lon, outlet_lat))
    # 存储湖泊栅格
    tif_co = ["COMPRESS=DEFLATE", "NUM_THREADS=8", "BIGTIFF=IF_SAFER", "TILED=YES"]
    raster.array2tif(lake_tif, lake_arr, geo_trans, proj, nd_value=0, dtype=raster.OType.I32, opt=tif_co)

    return outlets, basin_num, lakeRecords


def workflow_basin(basinInfoList, lakeDict, lake_num, basin_num, outlets, process_num,
                   lake_tif, basin_tif, dir_tif, src_offset, root, basin_out_folder):
    lakeFIDs = list(lakeDict.keys())
    hwDict = {}
    subBasinDict = {}
    downStreamCheckDict = {}

    # 并行处理各个子流域
    p_pool = Pool(process_num)
    mapFunc = partial(DealWithBasin.deal_with_single_basin, lake_tif=lake_tif, lake_num=lake_num,
                      bench_offset=src_offset, root=root, temp_folder=basin_out_folder)
    result = p_pool.map(mapFunc, basinInfoList)

    probe = 0
    for sub_result in result:
        code = basinInfoList[probe][1]
        probe += 1
        head_water, upBasin_num = sub_result.pop()
        hwDict[code] = head_water
        downStreamCheckDict[code] = upBasin_num
        for rec in sub_result:
            new_code = tuple(rec[0:2])
            subBasinDict[new_code] = dp.SubBasin(rec)

    # # 返回两个值，一个是所有的子流域，一个是承接上游的子流域
    # for basinInfo in basinInfoList:
    #     code = basinInfo[1]
    #     result = DealWithBasin.deal_with_single_basin(basinInfo, lake_tif, lake_num, src_offset, root, basin_out_folder)
    #     head_water = result.pop()
    #     hwDict[code] = head_water
    #     downStreamCheckDict[code] = len(result)
    #     for rec in result:
    #         new_code = tuple(rec[0:2])
    #         subBasinDict[new_code] = dp.SubBasin(rec)

    # 在上一步，假定所有的子流域都不流向湖泊
    # 现在要计算直接流入湖泊的子流域
    geo_trans = raster.get_raster_geotransform(lake_tif)
    ul_lon, width, _, ul_lat, _, height = geo_trans
    for i in range(lake_num + 1, basin_num + 1):
        outlet_ridx = int(outlets[i, 0])
        outlet_cidx = int(outlets[i, 1])
        src_outlet_ridx = src_offset[0] + outlet_ridx
        src_outlet_cidx = src_offset[1] + outlet_cidx
        code = int(raster.get_raster_value_by_loc(basin_tif, src_outlet_cidx, src_outlet_ridx))  # 原始流域
        outlet_dir = raster.get_raster_value_by_loc(dir_tif, src_outlet_cidx, src_outlet_ridx)
        sub_code = int(raster.get_raster_value_by_loc(lake_tif, outlet_cidx, outlet_ridx))  # 原始流域中的子流域
        down_ridx, down_cidx = get_downstream_index(outlet_ridx, outlet_cidx, outlet_dir)
        down_lake_value = int(raster.get_raster_value_by_loc(lake_tif, down_cidx, down_ridx))  # 下游湖泊
        # 更新流域信息
        new_code = (code, sub_code)
        sub_basin = subBasinDict[new_code]
        sub_basin.down_lake = lakeFIDs[down_lake_value - 1]
        sub_basin.outlet_lon = ul_lon + (outlet_cidx + 0.5) * width
        sub_basin.outlet_lat = ul_lat + (outlet_ridx + 0.5) * height
        # 不流向湖泊的子流域减1
        downStreamCheckDict[code] -= 1

    # 检查每个流域是否最多只有一个子流域流入非湖泊
    flag = False
    for key, value in downStreamCheckDict.items():
        if value > 1:
            print("Wrong sub-basin num in %d - %d" % (key, value))
            flag = True
    if flag is True:
        exit(-1)

    # 计算不流入湖泊的子流域的下游
    for key, sub_basin in subBasinDict.items():
        # 如果流入湖泊，直接跳过
        if sub_basin.down_lake > 0:
            continue
        down_code = sub_basin.down_code
        # 如果流向大海或流向内流区终点，也选择跳过
        if down_code <= 0:
            continue
        # 获取下游流域承接上游来水的部分
        down_sub_code = hwDict[down_code]
        # 如果没有承接上游来水的子流域，说明当前流域是一个内流区
        if down_sub_code is None:
            sub_basin.down_code = -1
        sub_basin.down_sub_code = down_sub_code

    # 存入数据库
    subBasinList = [sub_basin.export() for sub_basin in subBasinDict.values()]
    return subBasinList


def workflow(basin_db, alter_db, src_basin_code, basin_code, level, root, lake_shp, min_river_ths, process_num):
    mean_basin_area = dp.get_mean_basin_area(basin_db, level)
    lakeDict, lake_num = DealWithLake.filter_lake(lake_shp, mean_basin_area * 0.1)
    if lake_num <= 0:
        print("No big lake!")
        exit(-1)

    # 初始化流域替换表
    dp.create_alter_table(alter_db, level)
    # 单个流域矢量文件输出路径
    lake_out_folder = os.path.join(root, "lake_alter", "level_%d" % level, "lake")
    basin_out_folder = os.path.join(root, "lake_alter", "level_%d" % level, "basin")
    if not os.path.exists(lake_out_folder):
        os.makedirs(lake_out_folder)
    if not os.path.exists(basin_out_folder):
        os.makedirs(basin_out_folder)

    # 栅格文件路径
    basin_tif = os.path.join(root, "basin_result", "raster", "level_%d.tif" % level)  # 流域划分结果
    dir_tif = os.path.join(root, "raster", "dir.tif")  # 流向栅格数据
    lake_tif = os.path.join(root, "lake_alter", "level_%d_lake.tif" % level)  # 湖泊及湖泊上游流域

    # 解析工作路径
    str_src_code = str(src_basin_code)
    src_folder = os.path.join(root, *str_src_code)
    src_tif = os.path.join(src_folder, str_src_code + ".tif")
    src_db = os.path.join(src_folder, str_src_code + '.db')
    ul_offset = dp.get_ul_offset(src_db)

    # 处理湖泊
    outlets, basin_num, lakeRecords = workflow_lake(lakeDict, lake_num, lake_shp,
                                                    basin_tif, src_tif, ul_offset, root,
                                                    mean_basin_area, min_river_ths,
                                                    lake_tif, lake_out_folder)
    # 将湖泊处理结果存入到数据库中
    dp.insert_lake_info(alter_db, level, lakeRecords)

    # 处理流域
    subRecords = dp.get_sub_basin_info(basin_db, basin_code, level)
    basinRecords = workflow_basin(subRecords, lakeDict, lake_num, basin_num, outlets,
                                  process_num, lake_tif, basin_tif, dir_tif,
                                  ul_offset, root, basin_out_folder)
    # 将湖泊处理结果存入到数据库中
    dp.insert_basin_info(alter_db, level, basinRecords)
