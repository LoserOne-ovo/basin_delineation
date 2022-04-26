import os
import ctypes
import platform
import numpy as np


if platform.system() == "Windows":
    dll = ctypes.WinDLL(os.path.join(os.path.split(os.path.abspath(__file__))[0], "ws_dln106.dll"))
elif platform.system() == "Linux":
    dll = ctypes.CDLL(os.path.join(os.path.split(os.path.abspath(__file__))[0], "ws_dln106.so.64"))
else:
    raise RuntimeError("Unsupported platform %s" % platform.system())


def calc_reverse_dir(dir_arr):
    """
    Call C to calculate the reverse d8 flow direction
    :param dir_arr: d8 flow direction numpy array
    :return: reverse d8 flow direction numpy array
    """

    rows, cols = dir_arr.shape
    func = dll.calc_reverse_fdir

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.POINTER(ctypes.c_ubyte)
    ptr = func(dir_arr, rows, cols)

    arr_type = ctypes.c_ubyte * (rows * cols)
    address = ctypes.addressof(ptr.contents)
    result = np.frombuffer(arr_type.from_address(address), dtype=np.uint8)
    result = result.reshape((rows, cols))

    return result


def label(bin_image):
    """
    labeling four connected regions of binary image
    :param bin_image: input binary image
    :return: the label result
    """

    rows, cols = bin_image.shape
    label_4con = dll.label_4con

    label_4con.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=bin_image.shape, flags='C_CONTIGUOUS'),
                           ctypes.c_int32, ctypes.c_int32, ctypes.POINTER(ctypes.c_uint32)]
    label_4con.restype = ctypes.POINTER(ctypes.c_uint32)

    label_num = ctypes.pointer(ctypes.c_uint32(0))
    ptr = label_4con(bin_image, rows, cols, label_num)

    arr_type = ctypes.c_uint32 * (rows * cols)
    address = ctypes.addressof(ptr.contents)
    result = np.frombuffer(arr_type.from_address(address), dtype=np.uint32)
    result = result.reshape((rows, cols))
    return result, label_num.contents.value


def paint_up_mosaiced_uint8(idx_arr, re_dir_arr, basin_arr):
    """
    Labeling all upstream cells with the value of each outlet cell
    :param idx_arr: array location indexes of outlets
    :param re_dir_arr: reverse flow direction array
    :param basin_arr: sub basins labelled array
    :return:
    """

    rows, cols = basin_arr.shape
    ridx = idx_arr[:, 0].copy().astype(np.int32)
    cidx = idx_arr[:, 1].copy().astype(np.int32)
    idx_num = idx_arr.shape[0]
    compress_rate = 0.03
    func = dll.paint_up_mosaiced_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='C_CONTIGUOUS'),
                     ctypes.c_uint32, ctypes.c_double,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    res = func(ridx, cidx, idx_num, compress_rate, basin_arr, re_dir_arr, rows, cols)

    return res


def paint_up_uint8(idx_arr, colors, re_dir_arr, basin_arr):
    """
    Labeling all upstream cells of each outlet cell with given values
    :param idx_arr: array location indexes of outlets
    :param colors: given value array of each outlet
    :param re_dir_arr: reverse flow direction array
    :param basin_arr: sub basins labelled array
    :return:
    """
    rows, cols = basin_arr.shape
    idx_num = idx_arr.shape[0]
    compress_rate = 0.03
    func = dll.paint_up_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(idx_num, ), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=1, shape=(idx_num, ), flags='C_CONTIGUOUS'),
                     ctypes.c_uint32, ctypes.c_double,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    res = func(idx_arr, colors, idx_num, compress_rate, basin_arr, re_dir_arr, rows, cols)

    return res


def paint_up_uint32(idx_arr, colors, re_dir_arr, basin_arr):
    """
    Labeling all upstream cells of each outlet cell with given values
    :param idx_arr: array location indexes of outlets
    :param colors: given value array of each outlet
    :param re_dir_arr: reverse flow direction array
    :param basin_arr: sub basins labelled array
    :return:
    """
    rows, cols = basin_arr.shape
    idx_num = idx_arr.shape[0]
    compress_rate = 0.03
    func = dll.paint_up_uint32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(idx_num, ), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint32, ndim=1, shape=(idx_num, ), flags='C_CONTIGUOUS'),
                     ctypes.c_uint32, ctypes.c_double,
                     np.ctypeslib.ndpointer(dtype=np.uint32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    res = func(idx_arr, colors, idx_num, compress_rate, basin_arr, re_dir_arr, rows, cols)

    return res


def sink_merge_uint16(idx_arr, re_dir_arr, elv_arr, basin_arr):
    """
    Integrate uncoded sinks (whose number is larger than 255) into coded basins.
    :param idx_arr: array location indexes of sink bottoms
    :param re_dir_arr: reverse flow direction array
    :param elv_arr: elevation array
    :param basin_arr: sub basins labelled array
    :return:
    """
    rows, cols = basin_arr.shape
    sink_num = int(idx_arr.shape[0])
    compress_rate = 0.03
    func = dll.dissolve_sinks_uint16

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint16, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(sink_num, ), flags='C_CONTIGUOUS'),
                     ctypes.c_uint16, ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(basin_arr, re_dir_arr, elv_arr, idx_arr, sink_num, rows, cols, compress_rate)

    return res


def sink_merge_uint8(idx_arr, re_dir_arr, elv_arr, basin_arr):
    """
    Integrate uncoded sinks (whose number is less than 256) into coded basins.
    :param idx_arr: array location indexes of sink bottoms
    :param re_dir_arr: reverse flow direction array
    :param elv_arr: elevation array
    :param basin_arr: sub basins labelled array
    :return:
    """
    rows, cols = basin_arr.shape
    sink_num = idx_arr.shape[0]
    compress_rate = 0.03
    func = dll.dissolve_sinks_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(sink_num, ), flags='C_CONTIGUOUS'),
                     ctypes.c_uint8, ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(basin_arr, re_dir_arr, elv_arr, idx_arr, sink_num, rows, cols, compress_rate)

    return res


def pfafstetter(outlet_idx, basin_arr, re_dir_arr, upa_arr, sub_outlets, ths):
    """
    Divide an outflow basin into several (up to 9) sub basins.
    :param outlet_idx: array location indexes of the basin outlet
    :param basin_arr: sub basins labelled array
    :param re_dir_arr: reverse flow direction array
    :param upa_arr: up catchment area array
    :param sub_outlets: array location indexes of sub basin outlets
    :param ths: minimum river threshold
    :return:
    """

    rows, cols = re_dir_arr.shape
    func = dll.pfafstetter

    func.argtypes = [ctypes.c_int32, ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(11, 2), flags='C_CONTIGUOUS'),
                     ctypes.c_float, ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    sub_num = func(outlet_idx[0], outlet_idx[1], basin_arr, re_dir_arr, upa_arr, sub_outlets, ths, rows, cols)

    return int(sub_num)


def get_basin_envelopes(basin_arr, basin_envelopes):
    """
    Calculate the minimum bounding rectangle for each basin
    :param basin_arr: value range [1, 10], and 0 means no-data
    :param basin_envelopes: result array
    :return:
    """
    rows, cols = basin_arr.shape
    func = dll.get_basin_envelope_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=basin_envelopes.shape, flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32
    func(basin_arr, basin_envelopes, rows, cols)

    return 1


def update_island_label(island_label, island_paint_flag, t_island_num):
    """
    Update the label value of each island, making it attached to a coded basin
    :param island_label: the island 4-neighbor connected labeling result
    :param t_island_num: total island num
    :param island_paint_flag: update value array
    :return:
    """

    rows, cols = island_label.shape
    func = dll.update_island_label_uint32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint32, ndim=1, shape=island_paint_flag.shape, flags='C_CONTIGUOUS'),
                     ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    res = func(island_label, island_paint_flag, t_island_num, rows, cols)

    return res


def island_statistic(island_label, island_num, dir_arr, upa_arr):
    """
    Count the attributes of each island
    :param island_label: island labeled array
    :param island_num: total labeled island num
    :param dir_arr: d8 flow direction numpy array
    :param upa_arr: up catchment area array
    :return:
    """

    rows, cols = upa_arr.shape
    func = dll.island_statistic_uint32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint32, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     ctypes.c_uint32,
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(island_num,2), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(island_num,2), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, shape=(island_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, shape=(island_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(island_num,4), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    island_sample = np.zeros(shape=(island_num, 2), dtype=np.int32)
    island_center = np.zeros(shape=(island_num, 2), dtype=np.float32)
    island_area = np.zeros(shape=(island_num,), dtype=np.float32)
    island_ref_area = np.zeros(shape=(island_num,), dtype=np.float32)
    island_envelope = np.zeros(shape=(island_num, 4), dtype=np.int32)
    island_envelope[:, 0] = rows
    island_envelope[:, 1] = cols

    func(island_label, island_num, island_center, island_sample, island_area, island_ref_area,
         island_envelope, dir_arr, upa_arr, rows, cols)

    return island_center, island_sample, island_area, island_ref_area, island_envelope


def calc_single_pixel_area(re_dir_arr, upa_arr):
    """
    Calculate each specific cell area
    :param re_dir_arr: reverse flow direction array
    :param upa_arr: up catchment area array
    :return:
    """

    rows, cols = re_dir_arr.shape
    func = dll.calc_single_pixel_upa

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.POINTER(ctypes.c_float)

    ptr = func(re_dir_arr, upa_arr, rows, cols)

    arr_type = ctypes.c_float * (rows * cols)
    address = ctypes.addressof(ptr.contents)
    result = np.frombuffer(arr_type.from_address(address), dtype=np.float32)
    result = result.reshape((rows, cols))

    return result


def correct_lake_network_int32_c(lake_arr, dir_arr, re_dir_arr, upa_arr, river_ths):
    """
    修正湖泊边界处的河网
    :param lake_arr:    湖泊栅格矩阵， <= 0 代表非湖泊像元
    :param dir_arr:     流向栅格矩阵
    :param re_dir_arr:  逆流向栅格矩阵
    :param upa_arr:     汇流累积量栅格矩阵
    :param river_ths:   河网阈值
    :return:            无
    """

    rows, cols = lake_arr.shape
    func = dll.correct_lake_stream_1

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, flags='C_CONTIGUOUS'),
                     ctypes.c_float, ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    res = func(lake_arr, dir_arr, re_dir_arr, upa_arr, river_ths, rows, cols)


def paint_lake_hillslope_int32_c(lake_arr, max_lake_id, re_dir_arr, upa_arr, river_ths):

    rows, cols = lake_arr.shape
    func = dll.paint_lake_hillslope_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_float, ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    res = func(lake_arr, max_lake_id, re_dir_arr, upa_arr, river_ths, rows, cols)


def paint_lake_hillslope_2_int32_c(lake_arr, max_lake_id, dir_arr, re_dir_arr, upa_arr, river_ths):

    rows, cols = lake_arr.shape
    func = dll.paint_lake_hillslope_2_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_float, ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    res = func(lake_arr, max_lake_id, dir_arr, re_dir_arr, upa_arr, river_ths, rows, cols)


def paint_lake_local_catchment_int32_c(lake_arr, max_lake_id, re_dir_arr):
    
    rows, cols = lake_arr.shape
    func = dll.paint_lake_local_catchment_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    res = func(lake_arr, max_lake_id, re_dir_arr, rows, cols)


def paint_lake_whole_upper_catchment_int32_c(lake_arr, lake_id, re_dir_arr, result_arr):

    rows, cols = lake_arr.shape
    func = dll.paint_lake_upper_catchment

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    func(lake_arr, lake_id, result_arr, re_dir_arr, rows, cols)

    return 1


def create_lake_topology_int32_c(lake_arr, lake_num, dir_arr):

    rows, cols = lake_arr.shape
    func = dll.create_lake_topology

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, shape=(lake_num, ), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.POINTER(ctypes.c_int32)

    block_arr = np.zeros(shape=(lake_num,), dtype=np.int32)
    ptr = func(lake_arr, lake_num, block_arr, dir_arr, rows, cols)

    arr_type = ctypes.c_int32 * block_arr[-1]
    address = ctypes.addressof(ptr.contents)
    down_lake_arr = np.frombuffer(arr_type.from_address(address), dtype=np.int32)

    return down_lake_arr, block_arr


def create_route_between_lake_c(lake_arr, lake_num, dir_arr, upa_arr, dll):

    rows, cols = lake_arr.shape
    func = dll.create_route_between_lake

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32,
                     ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_uint64)]
    func.restype = ctypes.POINTER(ctypes.c_uint64)

    route_num = ctypes.pointer(ctypes.c_int32(0))
    result_length = ctypes.pointer(ctypes.c_uint64(0))
    ptr = func(lake_arr, lake_num, dir_arr, upa_arr, rows, cols, route_num, result_length)

    arr_type = ctypes.c_uint64 * result_length.contents.value
    address = ctypes.addressof(ptr.contents)
    result_arr = np.frombuffer(arr_type.from_address(address), dtype=np.uint64)

    return result_arr, route_num.contents.value



