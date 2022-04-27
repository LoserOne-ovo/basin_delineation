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
#    lake local catchmnet    #
##############################
def local_catchment(lake_tif, dir_tif, out_tif, out_shp):
    """ Delineate lake local catchment"""
    dir_arr, geo_trans, proj = raster.read_single_tif(dir_tif)
    lake_arr, _, _ = raster.read_single_tif(lake_tif)
    max_lake_id = np.max(lake_arr)
    
    re_dir_arr = cfunc.calc_reverse_dir(dir_arr)
    cfunc.paint_lake_local_catchment_int32_c(lake_arr, max_lake_id, re_dir_arr)
    raster.array2tif(out_tif, lake_arr, geo_trans, proj, nd_value=0, dtype=raster.OType.I32)


def polygonize_local_catchment(lake_lc_tif, out_shp):
    """ Convert raster layer to vector layer."""
    # Read GeoTIFF data
    lake_lc_ds = gdal.Open(lake_lc_tif)
    proj = lake_lc_ds.GetProjection()
    outband = lake_lc_ds.GetRasterBand(1)
    mask_band = outband.GetMaskBand()
    # Polygonize in memory vector datasource
    mem_vector_dirver = ogr.GetDriverByName("MEMORY")
    mem_vector_ds = mem_vector_dirver.CreateDataSource("temp")
    dst_layer = mem_vector_ds.CreateLayer("1", srs=osr.SpatialReference(wkt=proj))
    fd = ogr.FieldDefn("Lake_ID", ogr.OFTInteger)
    dst_layer.CreateField(fd)
    gdal.Polygonize(outband, mask_band, dst_layer, 0)
    
    lake_num = np.max(lake_arr)
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
    
    # Calculate the upstream and downstream relationship between lakes
    lake_lc_arr, geo_trans, proj = raster.read_single_tif(lake_tif)
    dir_arr, _, _ = raster.read_single_tif(dir_tif)
    lake_num = np.max(lake_lc_arr)
    topo_arr, block_arr = cfunc.create_lake_topology_int32_c(lake_lc_arr, lake_num, dir_arr)
    
    # Stored in sqlite database
    create_lake_topo_table(topo_db)
    lake_id_map = np.arange(start=1, stop=lake_num+1, step=1, dtype=np.int32)
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
    return (int(mapped_lake_id), None, int(down_lake_num), down_lake_list)


def expand_topo(topo_arr, block_arr, lake_id_map):
    """ Convert 1-D topo array into list"""
    return [map_lake_topo_record(topo_arr[block_arr[i-1] : block_arr[i]], block_arr[i] - block_arr[i-1], lake_id_map[i]) if i > 0 \
            else map_lake_topo_record(topo_arr[0: block_arr[0]], block_arr[0] - 0, lake_id_map[i]) \
            for i in range(block_arr.shape[0])]
    

def analyze_lake_topo(topo_db):
    
    # Query from sqlite database
    conn = sqlite3.connect(topo_db)
    cursor = conn.cursor()
    sql_line = "select lake_id, down_lake_num, down_lakes from %s where down_lake_num > 1;" % lake_topo_table_name
    cursor.execute(sql_line)
    result = cursor.fetchall()
    result_num = len(result)
    
    # Check whether a lake is a termial lake.
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
            cursor.execute("select down_lake_num, down_lakes from %s where lake_id = %d" % (table_name, up_lake_id))
            record = cursor.fetchone()
            down_lakes = struct.unpack('%di' % record[0], record[1])
            print("  %d: " % up_lake_id, down_lakes)
    
    conn.close()


def union_lake_whole_catchment(lc_shp, out_shp, topo_db, lake_num):
    """ To be updated. It will be better to use networkx."""
    # Query from sqlite database
    conn = sqlite3.connect(topo_db)
    cursor = conn.cursor()
    sql_line = "select lake_id, down_lake_num, down_lakes from %s where down_lake_num > 1;" % lake_topo_table_name
    cursor.execute(sql_line)
    result = cursor.fetchall()
    
    # Calculate the number of upstream lakes for each lake 
    upper_lake_num_arr = np.zeros((lake_num + 1, ), dtype=np.uint16)
    down_lake_dict = {}
    # Create updown_lake_dict
    for lake_id, down_lake_num, down_lakes in result:
        if down_lake_num > 0:
            down_lake_tuple = struct.unpack("%di" % down_lake_num, down_lakes)
            down_lake_list = list(down_lake_tuple)
            down_lake_list.remove(-1)
            down_lake_list.remove(lake_id)
            for down_lake_id in down_lake_list:
                upper_lake_num_arr[down_lake_id] += 1
            down_lake_dict[lake_id] = down_lake_list
        else:
            down_lake_dict[lake_id] = []

    processed_flag = np.zeros((lake_num + 1), dtype=np.uint16)
    change_num = 1
    while change_num > 0:
        change_num = 0
        for i in range(1, lake_num + 1):
            # First, process headwater lakes whose upper catchment equals its local catchment
            if processed_flag[i] == 0 and upper_lake_num_arr[i] == 0:
                pass
            # Second, reduce the upstream_lake_num of its downstream lakes.
            # Then, we can find new ‘headwater’ lakes.
            # If a 'headwater' lake has upstream lakes, UnionCascaded() all of their geometry
            # (local catchment of current lake, and upper catchment of its direct upstream lakes)
            # we can get the upper catchment of current lake.
            # Repeat until all lakes have been procecessed.

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
