# coding=utf-8
import numpy as np
import ctypes
from osgeo import gdal
from util import Array2D, ReadTif
from rtree import index
import time
import gc


dll = ctypes.WinDLL(r'basin_del101.dll')


def get_reverse_fdir(fdir):
    """
    Call C dll to calculate the reverse d8 flow direction
    :param fdir: d8 flow direction numpy array
    :return: reverse d8 flow direction numpy array
    """

    rows, cols = fdir.shape

    reverse_fdir = dll.reverse_fdir
    reverse_fdir.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=fdir.shape, flags='C_CONTIGUOUS'),
                             ctypes.c_int, ctypes.c_int]
    reverse_fdir.restype = ctypes.POINTER(ctypes.c_ubyte)
    result = reverse_fdir(fdir, rows, cols)

    arr_type = ctypes.c_ubyte * (rows * cols)
    address = ctypes.addressof(result.contents)
    arr = np.frombuffer(arr_type.from_address(address), dtype=np.uint8)
    arr = arr.reshape((rows, cols))
    return arr


def label(bin_image):
    """
    labeling four connected regions of binary image
    :param bin_image: input binary image
    :return: the label result
    """

    rows, cols = bin_image.shape
    label_4con = dll.label_4con
    label_4con.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=bin_image.shape, flags='C_CONTIGUOUS'),
                           ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]
    label_4con.restype = ctypes.POINTER(ctypes.c_uint)

    label_num = ctypes.pointer(ctypes.c_uint(0))
    result = label_4con(bin_image, rows, cols, label_num)

    arr_type = ctypes.c_uint * (rows * cols)
    address = ctypes.addressof(result.contents)
    arr = np.frombuffer(arr_type.from_address(address), dtype=np.uint)
    arr = arr.reshape((rows, cols))
    return arr, label_num.contents.value


def interrupt_edge(idxs, bin_map, value):
    """
    set the value of BIN_MAP at IDXS with VALUE
    :param idxs: 1D-indexs
    :param bin_map: binary array
    :param value: value to be set
    :return: None
    """

    for idx in idxs:
        [loc_i, loc_j] = idx
        bin_map[loc_i, loc_j] = value


def calc_gc(label_res, label_num):
    """
    calculate the geometry center of islands by C dll
    :param label_res:
    :param label_num:
    :return:
    """

    rows, cols = label_res.shape
    func = dll.calc_gc

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     ctypes.c_uint, ctypes.c_int, ctypes.c_int]
    func.restype = ctypes.POINTER(ctypes.c_uint64)

    ptr = func(label_res, label_num, rows, cols)

    arr_type = ctypes.c_uint64 * label_num
    address = ctypes.addressof(ptr.contents)
    result = np.frombuffer(arr_type.from_address(address), dtype=np.uint64)

    ridxs, cidxs = np.unravel_index(result, shape=(rows, cols))
    result = np.vstack((ridxs, cidxs))

    return result


def islands_merge(label_res, label_num, merge_flag, basin):

    rows, cols = basin.shape

    func = dll.islands_merge
    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint16, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_uint, ctypes.c_int, ctypes.c_int,
                     np.ctypeslib.ndpointer(dtype=np.uint16, ndim=1, flags='C_CONTIGUOUS')]
    func.restype = ctypes.c_int

    func(label_res, basin, label_num, rows, cols, merge_flag)

    return 1


def paint_upc(idx_array, re_fdir, basin):


    rows, cols = basin.shape
    ridx = idx_array[:, 0].copy().astype(np.uint)
    cidx = idx_array[:, 1].copy().astype(np.uint)
    idx_num = idx_array.shape[0]

    func = dll.paint_up
    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint, ndim=1, flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint, ndim=1, flags='C_CONTIGUOUS'),
                     ctypes.c_int, ctypes.c_uint,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint16, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS')]
    func.restype = ctypes.c_int

    res = func(ridx, cidx, cols, idx_num, re_fdir, basin)

    return res


def inner_merge(idx_array, outer_num, re_fdir, basin, dem):

    rows, cols = basin.shape
    ridx = idx_array[:, 0].copy().astype(np.uint)
    cidx = idx_array[:, 1].copy().astype(np.uint)
    inner_num = idx_array.shape[0]

    func = dll.paint_up_inner
    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint, ndim=1, flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint, ndim=1, flags='C_CONTIGUOUS'),
                     ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint16, ndim=2, flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, flags='C_CONTIGUOUS')]
    func.restype = ctypes.c_int

    res = func(ridx, cidx, cols, inner_num, outer_num, re_fdir, basin, dem)

    return res


def get_main_outlets(fdir, facc, num=4):
    """
    Find outer outlets with top NUM flow accumulation area and inner outlets
    :param fdir: d8 flow direction numpy array
    :param facc: d8 flow direction accumulation numpy array
    :param num: number of outer outlets
    :return: 1D-index of outer and inner outlets
    """

    inner_outlet_idx = (np.argwhere(fdir == 255))

    # temp_acc = facc.copy()
    # temp_acc[fdir != 0] = -1
    # outer_outlet_1d_idx = np.argsort(temp_acc.flatten())[-1 * num:]
    # outer_outlet_idx = [list(np.unravel_index(idx, shape)) for idx in outer_outlet_1d_idx]
    # del temp_acc
    # gc.collect()

    outer_outlet_idx = np.array([[4517, 2817],[6062,2994]])

    return outer_outlet_idx, inner_outlet_idx


def main_basin_delineation(fdir_arr, facc_arr, dem, out_path, out_geotransform, out_proj):

    # 读取数据
    re_fdir = get_reverse_fdir(fdir_arr)
    basin = np.zeros(fdir_arr.shape, dtype=np.uint16)

    outer_idx, inner_idx = get_main_outlets(fdir_arr, facc_arr, num=4)

    # 提取出所有的海陆边界，并使用4连通分类
    all_edge = Array2D.binarization(fdir_arr, front=[0], background=0)
    label_res, label_num = label(all_edge)

    outer_outlet_label = [label_res[loc_i, loc_j] for loc_i, loc_j in outer_idx]

    # 认为主要外流流域出水口所在的边界为大陆边界
    mainland_edge = Array2D.binarization(label_res, outer_outlet_label, background=0)

    del label_res  # 释放内存
    islands_edge = all_edge * (~(mainland_edge.astype(np.bool)))  # 计算其他岛屿边界的二值图
    del all_edge  # 释放内存
    gc.collect()

    # 使用主要外流流域出水口，打断大陆边界的连续性。
    # 据此将大陆边界分为若干段，每段边界认为是同一个大流域出水口的集合。
    # 其他的岛屿边界需最后会合并到这些大陆边界中。
    interrupt_edge(outer_idx, mainland_edge, 0)
    mainland_label_res, mainland_label_num = label(mainland_edge)

    del mainland_edge
    gc.collect()

    # 外流区编号， 并建立Rtree索引
    sp_idx = index.Index(interleaved=False)
    elem_id = 1
    color = 1
    for loc_i, loc_j in outer_idx:
        basin[loc_i, loc_j] = color
        cor = (loc_j, loc_j, loc_i, loc_i)
        sp_idx.insert(elem_id, cor, obj=color)
        elem_id += 1
        color += 1

    for i in range(1, mainland_label_num + 1):
        temp = np.argwhere(mainland_label_res == i)
        for j in range(temp.shape[0]):
            cor = (temp[j,1], temp[j,1], temp[j,0], temp[j,0])
            sp_idx.insert(elem_id, cor, obj=color+i-1)
            elem_id += 1

    mainland_label_res[mainland_label_res != 0] += color - 1
    basin = (basin + mainland_label_res).astype(np.uint16)

    del mainland_label_res
    gc.collect()

    # 提取其他岛屿的边界
    islands_edge_res, islands_edge_num = label(islands_edge)
    del islands_edge
    gc.collect()

    print('label completed!  ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    geo_center = calc_gc(islands_edge_res, islands_edge_num)
    islands_merge_flag = np.zeros((label_num,), dtype=np.uint16)

    for i in range(islands_edge_num):
        gc_cor = (geo_center[1,i], geo_center[1,i], geo_center[0,i], geo_center[0,i])
        islands_merge_flag[i] = list(sp_idx.nearest(gc_cor, objects="raw"))[0]

    islands_merge(islands_edge_res, islands_edge_num, islands_merge_flag, basin)


    del islands_edge_res
    gc.collect()
    print('islands merge completed!  ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    tag_idx_list = np.argwhere(basin != 0)

    paint_upc(tag_idx_list, re_fdir, basin)

    print('outer paint completed!  ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    outer_num = outer_idx.shape[0] + mainland_label_num
    inner_merge(inner_idx, outer_num, re_fdir, basin, dem)

    print('inner paint completed!  ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    options = ["COMPRESS=DEFLATE", "NUM_THREADS=8", "BIGTIFF=YES"]
    ReadTif.array2tif(out_path,basin,out_geotransform,out_proj,0,dtype=gdal.GDT_UInt16,opt=options)



if __name__ == '__main__':

    time_begin = time.time()
    print('begin at:  ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_begin)))


    fdir1 = ReadTif(r'..\..\Africa\dir\n30e030_dir.tif')
    fdir2 = ReadTif(r'..\..\Africa\dir\n25e030_dir.tif')
    out_geotransform = fdir1.geotransform
    out_proj = fdir1.proj
    merge_fdir1 = np.vstack((fdir1.data, fdir2.data))
    fdir1 = ReadTif(r'..\..\Africa\depart\n30e035_dir.tif')
    fdir2 = ReadTif(r'..\..\Africa\depart\n25e035_dir.tif')
    merge_fdir2 = np.vstack((fdir1.data, fdir2.data))
    merge_fdir = np.hstack((merge_fdir1,merge_fdir2))

    del fdir1, fdir2, merge_fdir1, merge_fdir2
    gc.collect()

    # facc1 = ReadTif(r'..\..\Africa\n30e030_upa.tif')
    # facc2 = ReadTif(r'..\..\Africa\n25e030_upa.tif')
    # merge_facc = np.vstack((facc1.data, facc2.data))
    # del facc1,facc2
    # gc.collect()

    dem1 = ReadTif(r'..\..\Africa\depart\n30e030_elv.tif')
    dem2 = ReadTif(r'..\..\Africa\depart\n25e030_elv.tif')
    merge_dem1 = np.vstack((dem1.data, dem2.data))
    dem1 = ReadTif(r'..\..\Africa\depart\n30e035_elv.tif')
    dem2 = ReadTif(r'..\..\Africa\depart\n25e035_elv.tif')
    merge_dem2 = np.vstack((dem1.data, dem2.data))
    merge_dem = np.hstack((merge_dem1, merge_dem2))

    del dem1, dem2, merge_dem1, merge_dem2
    gc.collect()

    merge_fdir[0, :] = 247
    merge_fdir[-1,:] = 247
    merge_fdir[:, 0] = 247
    merge_fdir[:,-1] = 247

    out_path = r'..\..\test\dem\test_basin03.tif'
    main_basin_delineation(merge_fdir, None, merge_dem, out_path, out_geotransform, out_proj)

    time_finish = time.time()
    print('finish at:  ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_finish)))
    print('Output consume:  ' + '{:.4f}'.format(time_finish - time_begin) + 's')
    print('done!')


