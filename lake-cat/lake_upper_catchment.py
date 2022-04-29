import sys
sys.path.append(r"../")
import struct
import sqlite3
import numpy as np
import networkx as nx
from util import raster
from util import interface as cfunc
from osgeo import gdal, ogr, osr


lake_topo_table_name = "lake_topo"


##############################
#    lake local catchment    #
##############################
def local_catchment(lake_tif, dir_tif, out_tif):
    """
    Delineate lake local catchment
    :param lake_tif:
    :param dir_tif:
    :param out_tif:
    :return:
    """
    """ """
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif)
    lake_arr, _, _ = raster.read_single_tif(lake_tif)
    max_lake_id = np.max(lake_arr)

    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    cfunc.paint_lake_local_catchment_int32_c(lake_arr, max_lake_id, re_dir_arr)
    raster.array2tif(out_tif, lake_arr, geo_trans, proj, nd_value=0, dtype=raster.OType.I32)


def polygonize_local_catchment(lake_lc_tif, out_shp):
    """
    Convert raster layer to vector layer.
    :param lake_lc_tif:
    :param out_shp:
    :return:
    """
    # Read GeoTIFF data
    lake_lc_ds = gdal.Open(lake_lc_tif)
    proj = lake_lc_ds.GetProjection()
    outband = lake_lc_ds.GetRasterBand(1)
    mask_band = outband.GetMaskBand()
    lake_arr = outband.ReadAsArray()
    lake_num = np.max(lake_arr)
    # Polygonize in memory vector datasource
    mem_vector_dirver = ogr.GetDriverByName("MEMORY")
    mem_vector_ds = mem_vector_dirver.CreateDataSource("temp")
    dst_layer = mem_vector_ds.CreateLayer("1", srs=osr.SpatialReference(wkt=proj))
    fd = ogr.FieldDefn("Lake_ID", ogr.OFTInteger)
    dst_layer.CreateField(fd)
    gdal.Polygonize(outband, mask_band, dst_layer, 0)

    # Create output shapefile
    shp_driver = ogr.GetDriverByName("ESRI Shapefile")
    out_ds = shp_driver.CreateDataSource(out_shp)
    out_layer = out_ds.CreateLayer("lake_local_catchment", srs=osr.SpatialReference(wkt=proj), geom_type=ogr.wkbMultiPolygon)
    out_layer.CreateField(fd)
    featureDefn = out_layer.GetLayerDefn()

    # Filter lake local catchment one by one
    for i in range(1, lake_num + 1):
        new_geom = ogr.Geometry(ogr.wkbMultiPolygon)
        dst_layer.SetAttributeFilter("Lake_ID=%d" % i)
        # merge polygons into a multipolygon
        for feature in dst_layer:
            new_geom.AddGeometry(feature.GetGeometryRef())
        if not new_geom.IsValid():
            new_geom = new_geom.Buffer(0.0)
        # Create feature
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(new_geom)
        feature.SetField("Lake_ID", i)
        out_layer.CreateFeature(feature)

    # Release
    mem_vector_ds.Destroy()
    out_layer.SyncToDisk()
    out_ds.Destroy()


#############################
#       lake topology       #
#############################
def create_lake_topology(lake_tif, dir_tif, topo_db):
    """

    :param lake_tif:
    :param dir_tif:
    :param topo_db:
    :return:
    """
    # Calculate the upstream and downstream relationship between lakes
    lake_lc_arr, geo_trans, proj = raster.read_single_tif(lake_tif)
    dir_arr, _, _ = raster.read_single_tif(dir_tif)
    lake_num = np.max(lake_lc_arr)
    topo_arr, block_arr = cfunc.create_lake_topology_int32_c(lake_lc_arr, lake_num, dir_arr)

    # Stored in sqlite database
    create_lake_topo_table(topo_db)
    lake_id_map = np.arange(start=1, stop=lake_num + 1, step=1, dtype=np.int32)
    insert_list = expand_topo(topo_arr, block_arr, lake_id_map)
    insert_many_lake_topo_record(topo_db, insert_list)


def create_lake_topo_table(topo_db):

    conn = sqlite3.connect(topo_db)
    cursor = conn.cursor()
    # Drop existed table
    cursor.execute("DROP TABLE IF EXISTS %s;" % lake_topo_table_name)
    # Create new table
    sql_line = """CREATE TABLE %s(
        lake_id int PRIMARY KEY,
        terminal tinyint,
        down_lake_num smallint,
        down_lakes blob
    );""" % lake_topo_table_name
    cursor.execute(sql_line)
    conn.commit()
    conn.close()


def insert_many_lake_topo_record(topo_db, ins_list):

    sql_line = "INSERT INTO %s VALUES(?, ?, ?, ?);" % lake_topo_table_name
    conn = sqlite3.connect(topo_db)
    cursor = conn.cursor()
    cursor.executemany(sql_line, ins_list)
    conn.commit()
    conn.close()


def map_lake_topo_record(down_lake_arr, down_lake_num, mapped_lake_id):

    if down_lake_num == 0:
        down_lake_list = None
    else:
        down_lake_list = struct.pack("%di" % down_lake_num, *down_lake_arr)
    return int(mapped_lake_id), None, int(down_lake_num), down_lake_list


def expand_topo(topo_arr, block_arr, lake_id_map):
    """ Convert 1-D topo array into list"""
    return [map_lake_topo_record(topo_arr[block_arr[i-1]: block_arr[i]], block_arr[i] - block_arr[i-1], lake_id_map[i]) if i > 0
            else map_lake_topo_record(topo_arr[0: block_arr[0]], block_arr[0] - 0, lake_id_map[i])
            for i in range(block_arr.shape[0])]


def analyze_lake_topo(topo_db):

    # Query from sqlite database
    conn = sqlite3.connect(topo_db)
    cursor = conn.cursor()
    sql_line = "select lake_id, down_lake_num, down_lakes from %s where down_lake_num > 1;" % lake_topo_table_name
    cursor.execute(sql_line)
    result = cursor.fetchall()

    # Check whether a lake is a terminal lake.
    # A terminal lake should not have downstream lakes.
    for lake_id, down_lake_num, down_lakes in result:
        lake_list = struct.unpack("%di" % down_lake_num, down_lakes)
        if lake_id in lake_list or -1 in lake_list:
            print(lake_id, lake_list)

    # Check whether there are cycles in lake topology.
    DG = nx.DiGraph()
    for lake_id, down_lake_num, down_lakes_blob in result:
        down_lakes = struct.unpack('%di' % down_lake_num, down_lakes_blob)
        for down_lake_id in down_lakes:
            if down_lake_id != -1 and down_lake_id != lake_id:
                DG.add_edge(lake_id, down_lake_id)

    print(nx.is_directed_acyclic_graph(DG))
    cycles = nx.simple_cycles(DG)
    for cycle in cycles:
        print("cycle:", tuple(cycle))
        for up_lake_id in cycle:
            cursor.execute("select down_lake_num, down_lakes from %s where lake_id = %d" % (lake_topo_table_name, up_lake_id))
            record = cursor.fetchone()
            down_lakes = struct.unpack('%di' % record[0], record[1])
            print("  %d: " % up_lake_id, down_lakes)

    conn.close()


def union_lake_whole_catchment(lc_shp, out_shp, topo_db, lake_num):
    """
    To be updated. It will be better to use networkx.
    Make sure that there is no cycle in the lake topology graph.
    :param lc_shp:
    :param out_shp:
    :param topo_db:
    :param lake_num:
    :return:
    """
    # Query from sqlite database
    conn = sqlite3.connect(topo_db)
    cursor = conn.cursor()
    sql_line = "select lake_id, down_lake_num, down_lakes from %s where down_lake_num > 1;" % lake_topo_table_name
    cursor.execute(sql_line)
    result = cursor.fetchall()

    # Create an array to record whether the whole up slope catchment of each lake has been built
    processed_flag = np.zeros((lake_num + 1), dtype=np.bool)
    processed_flag[0] = 1
    # Create an array to store the number of upstream lakes for each lake
    upper_lake_num_arr = np.zeros((lake_num + 1, ), dtype=np.uint16)
    # Create updown_lake_dict
    updown_lake_dict = {}
    for lake_id, down_lake_num, down_lakes in result:
        # Create sub-dict for single lake
        updown_lake_dict[lake_id] = {"uplake_num": 0, "uplakes": [], "downlake_num": 0, "downlakes": []}

    # Update updown stream info
    for lake_id, down_lake_num, down_lakes in result:
        # when a lake have downstream lakes
        if down_lake_num > 0:
            down_lake_tuple = struct.unpack("%di" % down_lake_num, down_lakes)
            down_lake_list = list(down_lake_tuple)
            # remove terminal lake info
            down_lake_list.remove(-1)
            down_lake_list.remove(lake_id)
            mod_down_lake_num = len(down_lake_list)
            if mod_down_lake_num > 0:
                # Add upstream lake info
                for down_lake_id in down_lake_list:
                    upper_lake_num_arr[down_lake_id] += 1
                    updown_lake_dict[down_lake_id]["uplake_num"] += 1
                    updown_lake_dict[down_lake_id]["uplakes"].append(lake_id)
                # Update downstream lakes of current lake
                updown_lake_dict[lake_id]["downlake_num"] = mod_down_lake_num
                updown_lake_dict[lake_id]["downlakes"] = down_lake_list

    # Read lake local catchment datasource
    lc_ds = ogr.Open(lc_shp)
    lc_layer = lc_ds.Getlayer()
    # Create output lake whole catchment datasource
    shp_driver = ogr.GetDriverByName("ESRI Shapefile")
    wc_ds = shp_driver.CreateDataSource(out_shp)
    wc_layer = wc_ds.CreateLayer("whole catchment", srs=lc_layer.GetSpatialRef(), geom_type=ogr.wkbMultiPolygon)
    field = ogr.FieldDefn("LakeID", ogr.OFTInteger)
    wc_layer.CreateField(field)
    featureDefn = wc_layer.GetLayerDefn()

    """
        1. First, process headwater lakes whose upper catchment equals its local catchment.
        2. Second, reduce the upstream_lake_num of its downstream lakes.
        3. Then, we can find new ‘headwater’ lakes.
        4. If a 'headwater' lake has upstream lakes, UnionCascaded() all of their geometry
    (local catchment of current lake, and upper catchment of its direct upstream lakes),
    we can get the upper catchment of current lake.
        5. Repeat until all lakes have been processed.
    """

    # First, process headwater lakes whose upper catchment equals its local catchment
    manageable_lakes = np.argwhere((processed_flag == 0) & (upper_lake_num_arr == 0))
    while manageable_lakes.shape[0] > 0:
        for lake_id in manageable_lakes:
            out_geom = ogr.Geometry(ogr.wkbMultiPolygon)
            # Add local catchment of current lake
            lc_layer.SetAttributeFilter("LakeID=%d" % lake_id)
            for feature in lc_layer:
                out_geom.AddGeometry(feature.GetGeometryRef())
            # Add whole lake catchment of upstream lakes
            for up_lake_id in updown_lake_dict[lake_id]["uplakes"]:
                lc_layer.SetAttributeFilter("LakeID=%d" % up_lake_id)
                for feature in lc_layer:
                    out_geom.AddGeometry(feature.GetGeometryRef())
            # Union Cascaded
            out_geom = out_geom.UnionCascaded()

            # Create output feature
            out_feature = ogr.Feature(featureDefn)
            out_feature.SetGeometry(out_geom)
            out_feature.SetField("LakeID", lake_id)
            wc_layer.CreateFeature(out_feature)

            processed_flag[lake_id] = 1
            # reduce the number of upstream lakes for downstream lakes of current lake
            for down_lake_id in updown_lake_dict[lake_id]["downlakes"]:
                upper_lake_num_arr[down_lake_id] -= 1
            # Recalculate "head water" lakes
            manageable_lakes = np.argwhere((processed_flag == 0) & (upper_lake_num_arr == 0))

    wc_layer.SyncToDisk()
    wc_ds.Destroy()
    lc_ds.Destroy()

    # Judge whether there are lakes whose whole catchment couldn't be built.
    if np.sum(processed_flag == 0) > 0:
        print("There are cycles in lake topology.")


if __name__ == "__main__":

    src_lake_tif = r""
    src_dir_tif = r""
    lc_lake_tif = r""
    lc_lake_shp = r""
    lake_topology_db = r""

    # local_catchment(src_lake_tif, src_dir_tif, lc_lake_tif, lc_lake_shp)
    # create_lake_topology(src_lake_tif, src_dir_tif, lake_topology_db)
    # analyze_lake_topo(lake_topology_db)
    # polygonize_local_catchment(lc_lake_tif, lc_lake_shp)
