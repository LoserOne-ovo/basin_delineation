import os
import sys
sys.path.append(r"../")
import pickle
import sqlite3
import numpy as np
import networkx as nx
from osgeo import ogr
from util import raster
from util import interface as cfunc


class topoQuery(object):

    @staticmethod
    def get_basin_topo_info(filePath):
        """
        Query basin topology information from shapefile
        @param filePath: path of the basin shapefile
        @return: list of tuple(current basin, downstream basin)
        """
        inDs = ogr.Open(filePath)
        inLayer = inDs.GetLayer(0)

        IdFieldName = "Basin_ID"
        IdFieldIndex = inLayer.FindFieldIndex(IdFieldName, 1)
        downIdFieldName = "Down_ID"
        downIdFieldIndex = inLayer.FindFieldIndex(downIdFieldName, 1)

        result = [(feature.GetField(IdFieldIndex), feature.GetField(downIdFieldIndex)) for feature in inLayer]

        inDs.Destroy()
        return result

    @staticmethod
    def get_basin_topo_info_sqlite(filePath):
        """
        Query basin topology information from geopackage
        @param filePath: path of the basin geopackage
        @return: list of tuple(current basin, downstream basin)
        """
        attrTableName = "data"
        idFieldName = "Basin_ID"
        downIdFieldName = "Down_ID"

        conn = sqlite3.connect(filePath)
        cursor = conn.cursor()
        sql_line = "select %s, %s from %s;" % (idFieldName, downIdFieldName, attrTableName)
        cursor.execute(sql_line)
        result = cursor.fetchall()

        conn.close()
        return result

    @staticmethod
    def create_topo_dict(filePath, outDictPath, sqlQuery=False, nxModel=False):
        """
        Create topology structure file for upstream and downstream routing
        @param filePath: path of the basin file
        @param outDictPath: path of the topology struct file
        @param sqlQuery: true if the basin file in format of geopackage
        @param nxModel: method used to create topology structure, python dictionary in default
        @return:
        """
        # Query basin topology information
        if sqlQuery is True:
            topoInfo = topoQuery.get_basin_topo_info_sqlite(filePath)
        else:
            topoInfo = topoQuery.get_basin_topo_info(filePath)

        # Create topology structure
        # networkx method
        if nxModel is True:
            # 构建有向五环图
            G = nx.DiGraph()
            G.add_edges_from(topoInfo)
            # 保存文件
            nx.write_gpickle(G, outDictPath)
        # Python dictionary method (recommended)
        else:
            # 构建上下游字典
            downDict = {}
            upDict = {}
            # 构建下游字典，同时初始化上游字典
            for cur_basin, down_basin in topoInfo:
                downDict[cur_basin] = down_basin
                upDict[cur_basin] = []
            # 构建上游字典
            for cur_basin, down_basin in downDict.items():
                if down_basin > 0:
                    upDict[down_basin].append(cur_basin)
            # 保存文件
            topoD = {
                "upStreamDict": upDict,
                "downStreamDict": downDict,
            }
            with open(outDictPath, "wb") as fs:
                pickle.dump(topoD, fs)
            fs.close()

    @staticmethod
    def locate_basin_by_point(lon, lat, filePath):
        """
        Query the basin where POI is located
        @param lon: longitude of POI
        @param lat: latitude of POI
        @param filePath: file path of basin geopackage
        @return: id of the basin
        """
        flag = True
        sql_line = "SELECT Basin_id FROM data WHERE Contains(geom, GeomFromText('POINT (%f %f)', 4326));" % (lon, lat)

        inDs = ogr.Open(filePath)
        resLayer = inDs.ExecuteSQL(sql_line)
        resNum = resLayer.GetFeatureCount()
        # 判断是否有正确的空间查询结果
        if resNum <= 0:
            print("No basin found!")
            flag = False
        elif resNum > 1:
            print("More than one basin found!")
            flag = False
        else:
            pass

        if flag is False:
            inDs.ReleaseResultSet(resLayer)
            inDs.Destroy()
            exit(-1)

        feature = resLayer.GetFeature(0)
        result = feature.GetField(0)
        inDs.ReleaseResultSet(resLayer)
        inDs.Destroy()

        return result

    @staticmethod
    def create_output_shp(basinList, filePath, outPath):
        """

        @param basinList:
        @param filePath:
        @param outPath:
        @return:
        """

        inDs = ogr.Open(filePath)
        inLayer = inDs.GetLayer()
        srs = inLayer.GetSpatialRef()
        featureDefn = inLayer.GetLayerDefn()

        shpDriver = ogr.GetDriverByName("ESRI Shapefile")
        outDs = shpDriver.CreateDataSource(outPath)
        outLayer = outDs.CreateLayer("data", srs=srs, geom_type=ogr.wkbMultiPolygon)
        # Add field values from input Layer
        for i in range(0, featureDefn.GetFieldCount()):
            fieldDefn = featureDefn.GetFieldDefn(i)
            outLayer.CreateField(fieldDefn)

        conList = ",".join(map(str, basinList))
        table_name = "data"
        sql_column_name = "Basin_ID"
        sql_line = "select * from %s where %s in (%s);" % (table_name, sql_column_name, conList)

        resLayer = inDs.ExecuteSQL(sql_line)
        for feature in resLayer:
            outLayer.CreateFeature(feature)
        outLayer.SyncToDisk()
        outDs.Destroy()
        inDs.ReleaseResultSet(resLayer)
        inDs.Destroy()

    @staticmethod
    def find_upstream_basins(outlet_basin, dictPath, nxModel=False):

        if nxModel is True:
            G = nx.read_gpickle(dictPath)
            subGraph = nx.bfs_tree(G, outlet_basin, reverse=True)
            result = subGraph.nodes()

        else:
            # 加载拓扑字典
            with open(dictPath, "rb") as fs:
                topoDict = pickle.load(fs)
            fs.close()
            # 初始化返回结果
            upDict = topoDict["upStreamDict"]
            result = []
            query_queue = [outlet_basin]
            num = 1
            # 查询上游
            while num > 0:
                temp = query_queue.pop()
                result.append(temp)
                num -= 1
                ups = upDict[temp]
                up_num = len(ups)
                if up_num > 0:
                    num += up_num
                    query_queue.extend(ups)

        return result

    @staticmethod
    def workflow(lon, lat, inFile, outFile, dictFile, nxModel=False):
        """
        根据坐标从矢量文件中提取上游流域范围（默认所坐标点位于主河道上）。
        @param lon:
        @param lat:
        @param inFile:
        @param outFile:
        @param dictFile:
        @param nxModel:
        @return:
        """

        outlet_basin = topoQuery.locate_basin_by_point(lon, lat, inFile)
        basinList = topoQuery.find_upstream_basins(outlet_basin, dictFile, nxModel)
        topoQuery.create_output_shp(basinList, inFile, outFile)

        return 0



class rasterExtract(object):

    bp_table_name = 'basin_property'
    gt_table_name = 'geo_transform'
    mo_table_name = 'main_outlets'
    sb_table_name = 'sink_bottoms'
    is_table_name = 'islands'
    basin_table_name = "property"
    sink_table_name = "sink"

    @staticmethod
    def query_basin_type(database, code):
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("select type from %s where code=%s;" % (rasterExtract.basin_table_name, code))
        result = cursor.fetchone()
        if result is None:
            print("No such basin %s!" % code)
        conn.close()
        return result[0]

    @staticmethod
    def get_upper_basin_code(code, database):
        """
        计算上游流域的编码，从而获取当前流域的入流点
        :param code:
        :param database:
        :return:
        """
        temp_code = code
        while True:
            last_code = temp_code[-1]
            if last_code != '9':
                upper_code = code[:-1] + str(int(last_code) + 1)
                upper_type = rasterExtract.query_basin_type(database, upper_code)
                if upper_type == 1 or upper_type == 2:
                    break
            temp_code = temp_code[:-1]
        return upper_code

    @staticmethod
    def query_basin_ul_offset(database, code):
        """
        从汇总数据库中，查询流域在栅格中的相对位置
        :param database:
        :param code:
        :return:
        """
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("select ul_con_ridx, ul_con_cidx, rows, cols from %s where code=%s;" %
                       (rasterExtract.basin_table_name, code))
        result = cursor.fetchone()
        if result is None:
            print("No such basin %s!" % code)
        conn.close()
        return result

    @staticmethod
    def query_basin_outlet_idx(database, code):
        """
        :param database:
        :param code:
        :return:
        """
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("select outlet_ridx, outlet_cidx from %s where code=%s;" %
                       (rasterExtract.basin_table_name, code))
        result = cursor.fetchone()
        if result is None:
            print("No such basin %s!" % code)
        conn.close()
        return result

    @staticmethod
    def check_on_mainstream(lon, lat, code, database, root):
        """

        :param lon:
        :param lat:
        :param code:
        :param database:
        :param root:
        :return:
        """
        # 计算上游流域
        upper_code = rasterExtract.get_upper_basin_code(code, database)
        # 计算上游流域在当前流域的入流点
        upper_ul_ridx, upper_ul_cidx, upper_rows, upper_cols = rasterExtract.query_basin_ul_offset(database, upper_code)
        local_ul_ridx, local_ul_cidx, local_rows, local_cols = rasterExtract.query_basin_ul_offset(database, code)
        # 计算上游流域的出水口的位置
        outlet_ridx, outlet_cidx = rasterExtract.query_basin_outlet_idx(database, code)
        # 并作为当前流域的入流点
        inlet_global_ridx = upper_ul_ridx + outlet_ridx
        inlet_global_cidx = upper_ul_cidx + outlet_cidx
        inlet_ridx = inlet_global_ridx - local_ul_ridx
        inlet_cidx = inlet_global_cidx - local_ul_cidx
        # 计算上游流域出水口的流向
        dir_tif = os.path.join(root, "src_dir.tif")
        inlet_dir = int(raster.get_raster_value_by_loc(dir_tif, inlet_global_cidx, inlet_global_ridx))
        # 读取当前流域的流向数据
        dir_arr, geo_trans, proj, nd_value = raster.read_tif_by_shape(dir_tif, local_ul_ridx, local_ul_cidx,
                                                                      local_rows, local_cols)
        # 计算用户输入出水口的行列索引
        outlet_ridx, outlet_cidx = raster.cor2idx(lon, lat, geo_trans)
        # 判断用户给定的出水口是否在干流上
        result = cfunc.check_outlet_on_mainstream(outlet_ridx, outlet_cidx, inlet_ridx, inlet_cidx, inlet_dir, dir_arr)
        return result

    @staticmethod
    def build_watershed(lon, lat, code, database, root, clip_method, res_option):
        """
        在给定的流域中，计算给定流域出水口的上游。
        :param lon:
        :param lat:
        :param code:
        :param database:
        :param root:
        :param clip_method:
        :param res_option:
        :return:
        """
        # 获取栅格文件路径
        dir_tif = os.path.join(root, "src_dir.tif")
        upa_tif = os.path.join(root, "src_upa.tif")
        elv_tif = os.path.join(root, "src_elv.tif")
        # 读取流向栅格数据
        local_ul_ridx, local_ul_cidx, local_rows, local_cols = rasterExtract.query_basin_ul_offset(database, code)
        dir_arr, geo_trans, proj, dir_nd_value = \
            raster.read_tif_by_shape(dir_tif, local_ul_ridx, local_ul_cidx, local_rows,local_cols)
        # 计算出水口在矩阵中的行列索引
        outlet_ridx, outlet_cidx = raster.cor2idx(lon, lat, geo_trans)
        # 初始化结果矩阵
        basin = np.zeros(dir_arr.shape, dtype=np.uint8)
        # 计算逆流向矩阵
        re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
        # 追踪上游
        outlet_idxs = np.zeros(shape=(1,), dtype=np.uint64)
        outlet_colors = np.zeros(shape=(1,), dtype=np.uint8)
        outlet_idxs[0] = outlet_ridx * dir_arr.shape[1] + outlet_cidx
        outlet_colors[0] = 1
        cfunc.paint_up_uint8(outlet_idxs, outlet_colors, re_dir_arr, basin)
        # 计算流域边界envelope
        envelopes = np.zeros(shape=(2, 4), dtype=np.int32)
        envelopes[:, 0] = dir_arr.shape[0]
        envelopes[:, 1] = dir_arr.shape[1]
        cfunc.get_basin_envelopes(basin, envelopes)

        # 裁剪边界
        if clip_method == 0:
            min_ridx = envelopes[1, 0]
            min_cidx = envelopes[1, 1]
            max_ridx = envelopes[1, 2]
            max_cidx = envelopes[1, 3]
        else:
            min_ridx = envelopes[1, 0] - 1
            min_cidx = envelopes[1, 1] - 1
            max_ridx = envelopes[1, 2] + 1
            max_cidx = envelopes[1, 3] + 1

        # 生成文件
        sub_ul_lon = geo_trans[0] + min_cidx * geo_trans[1]
        sub_ul_lat = geo_trans[3] + min_ridx * geo_trans[5]
        sub_geotrans = (sub_ul_lon, geo_trans[1], geo_trans[2], sub_ul_lat, geo_trans[4], geo_trans[5])
        mask_arr = basin[min_ridx:max_ridx + 1, min_cidx:max_cidx + 1] != 1
        if not os.path.exists(res_option["folder"]):
            os.mkdir(res_option["folder"])
        # 流向
        if res_option["dir"] is True:
            out_arr = dir_arr[min_ridx:max_ridx + 1, min_cidx:max_cidx + 1].copy()
            out_arr[mask_arr] = dir_nd_value
            out_fn = os.path.join(res_option["folder"], res_option["id"] + "_dir.tif")
            raster.array2tif(out_fn, out_arr, sub_geotrans, proj, nd_value=dir_nd_value, dtype=raster.OType.Byte)
        # 汇流累积量
        if res_option["upa"] is True:
            upa_arr, _, _, upa_nd_value = \
                raster.read_tif_by_shape(upa_tif, local_ul_ridx, local_ul_cidx, local_rows, local_cols)
            out_arr = upa_arr[min_ridx:max_ridx + 1, min_cidx:max_cidx + 1].copy()
            out_arr[mask_arr] = upa_nd_value
            out_fn = os.path.join(res_option["folder"], res_option["id"] + "_upa.tif")
            raster.array2tif(out_fn, out_arr, sub_geotrans, proj, nd_value=upa_nd_value, dtype=raster.OType.F32)
        # 高程
        if res_option["elv"] is True:
            elv_arr, _, _, elv_nd_value = \
                raster.read_tif_by_shape(elv_tif, local_ul_ridx, local_ul_cidx, local_rows, local_cols)
            out_arr = elv_arr[min_ridx:max_ridx + 1, min_cidx:max_cidx + 1].copy()
            out_arr[mask_arr] = elv_nd_value
            out_fn = os.path.join(res_option["folder"], res_option["id"] + "_elv.tif")
            raster.array2tif(out_fn, out_arr, sub_geotrans, proj, nd_value=elv_nd_value, dtype=raster.OType.F32)
        # 矢量shp
        if res_option["bound"] is True:
            out_arr = np.ones(mask_arr.shape, dtype=np.uint8)
            out_arr[mask_arr] = 0
            out_fn = os.path.join(res_option["folder"], res_option["id"] + "_bound.shp")
            raster.raster2shp_mem(out_fn, out_arr, sub_geotrans, proj, nd_value=0, dtype=raster.OType.Byte)

    @staticmethod
    def extract_basin(lon, lat, code, root, clip_method, res_option):
        """
        在给定的流域中，计算给定流域出水口的上游。
        :param lon:
        :param lat:
        :param code:
        :param root:
        :param clip_method:
        :param res_option:
        :return:
        """
        # 检查流域类型
        database = os.path.join(root, "basin.db")
        basin_type = rasterExtract.query_basin_type(database, code)
        # 如果流域类型
        if basin_type == 2:
            flag = rasterExtract.check_on_mainstream(lon, lat, code, database, root)
            print(flag)
            if flag == 0:
                rasterExtract.build_watershed(lon, lat, code, database, root, clip_method, res_option)
            else:
                parent_code = code[:-1]
                if len(parent_code) == 1:
                    rasterExtract.build_watershed(lon, lat, code, database, root, clip_method, res_option)
                else:
                    rasterExtract.extract_basin(lon, lat, parent_code, root, clip_method, res_option)
        else:
            rasterExtract.build_watershed(lon, lat, code, database, root, clip_method, res_option)

        return 1


if __name__ == "__main__":

    # 闽江
    outlet_lon = 119.524
    outlet_lat = 26.055
    outFilePath = r"D:\Project\minjiang\shp\mj_bound2.shp"

    inFilePath = r"D:\demo\Asia\lake_result\level_12.gpkg"
    dictFilePath = r"D:\demo\Asia\lake_result\Dictionary\level_12.dic"
    topoQuery.workflow(outlet_lon, outlet_lat, inFilePath, outFilePath, dictFilePath)
