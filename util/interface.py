import os
import ctypes
import platform
import numpy as np

if platform.system() == "Windows":
    dll = ctypes.WinDLL(os.path.join(os.path.split(os.path.abspath(__file__))[0], "ws_dln107.dll"))
elif platform.system() == "Linux":
    dll = ctypes.CDLL(os.path.join(os.path.split(os.path.abspath(__file__))[0], "ws_dln107.so.64"))
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
    labeling four connected mRegions of binary image
    :param bin_image: input binary image
    :return: the label result
    """

    rows, cols = bin_image.shape
    label_4con = dll.label_4con

    label_4con.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=bin_image.shape, flags='C_CONTIGUOUS'),
                           ctypes.c_int32, ctypes.c_int32, ctypes.POINTER(ctypes.c_int32)]
    label_4con.restype = ctypes.POINTER(ctypes.c_int32)

    label_num = ctypes.pointer(ctypes.c_int32(0))
    ptr = label_4con(bin_image, rows, cols, label_num)

    arr_type = ctypes.c_int32 * (rows * cols)
    address = ctypes.addressof(ptr.contents)
    result = np.frombuffer(arr_type.from_address(address), dtype=np.int32)
    result = result.reshape((rows, cols))

    return result, label_num.contents.value


def paint_up_mosaiced_uint8(re_dir_arr, basin_arr):
    """
    Labeling all upstream cells with the value of each outlet cell
    :param re_dir_arr: reverse flow direction array
    :param basin_arr: sub basins labelled array
    :return:
    """

    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.paint_up_mosaiced_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(basin_arr, re_dir_arr, rows, cols, compress_rate)

    return res


def paint_up_mosaiced_uint16(re_dir_arr, basin_arr):
    """
    Labeling all upstream cells with the value of each outlet cell
    :param re_dir_arr: reverse flow direction array
    :param basin_arr: sub basins labelled array
    :return:
    """

    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.paint_up_mosaiced_uint16

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint16, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(basin_arr, re_dir_arr, rows, cols, compress_rate)

    return res


def paint_up_mosaiced_int32(re_dir_arr, basin_arr):
    """
    Labeling all upstream cells with the value of each outlet cell
    :param re_dir_arr: reverse flow direction array
    :param basin_arr: sub basins labelled array
    :return:
    """

    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.paint_up_mosaiced_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(basin_arr, re_dir_arr, rows, cols, compress_rate)

    return res


def paint_up_mosaiced_uint32(re_dir_arr, basin_arr):
    """
    Labeling all upstream cells with the value of each outlet cell
    :param re_dir_arr: reverse flow direction array
    :param basin_arr: sub basins labelled array
    :return:
    """

    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.paint_up_mosaiced_uint32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(basin_arr, re_dir_arr, rows, cols, compress_rate)

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
    idx_num = idx_arr.shape[0]
    if idx_num <= 0:
        return -1

    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.paint_up_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_uint32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(idx_arr, colors, idx_num, basin_arr, re_dir_arr, rows, cols, compress_rate)

    return res


def paint_up_uint16(idx_arr, colors, re_dir_arr, basin_arr):
    """
    Labeling all upstream cells of each outlet cell with given values
    :param idx_arr: array location indexes of outlets
    :param colors: given value array of each outlet
    :param re_dir_arr: reverse flow direction array
    :param basin_arr: sub basins labelled array
    :return:
    """
    idx_num = idx_arr.shape[0]
    if idx_num <= 0:
        return -1

    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.paint_up_uint16

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint16, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_uint32,
                     np.ctypeslib.ndpointer(dtype=np.uint16, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(idx_arr, colors, idx_num, basin_arr, re_dir_arr, rows, cols, compress_rate)

    return res


def paint_up_int32(idx_arr, colors, re_dir_arr, basin_arr):
    """
    Labeling all upstream cells of each outlet cell with given values
    :param idx_arr: array location indexes of outlets
    :param colors: given value array of each outlet
    :param re_dir_arr: reverse flow direction array
    :param basin_arr: sub basins labelled array
    :return:
    """
    idx_num = idx_arr.shape[0]
    if idx_num <= 0:
        return -1
    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.paint_up_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_uint32,
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(idx_arr, colors, idx_num, basin_arr, re_dir_arr, rows, cols, compress_rate)

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
    idx_num = idx_arr.shape[0]
    if idx_num <= 0:
        return -1

    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.paint_up_uint32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint32, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_uint32,
                     np.ctypeslib.ndpointer(dtype=np.uint32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(idx_arr, colors, idx_num, basin_arr, re_dir_arr, rows, cols, compress_rate)

    return res


def sink_union(sink_num, basin_arr):
    """

    :param sink_num:
    :param basin_arr:
    :return:
    """
    rows, cols = basin_arr.shape
    sink_union_flag = np.zeros((sink_num + 1,), dtype=np.int32)
    sink_merge_flag = np.zeros((sink_num + 1,), dtype=np.int32)
    if sink_num < 1:
        return sink_union_flag, sink_merge_flag

    func = dll.sink_union_int32
    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, shape=(sink_num + 1,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, shape=(sink_num + 1,), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    result = func(sink_union_flag, sink_merge_flag, sink_num, basin_arr, rows, cols)
    if result < 0:
        print(result)
        raise RuntimeError("Error occurred when union sinks!")
    return sink_union_flag, sink_merge_flag, result


def get_region_attached_basin(sink_idxs, re_dir_arr, elv_arr, basin_arr):
    """

    :param sink_idxs:
    :param re_dir_arr:
    :param elv_arr:
    :param basin_arr:
    :return:
    """
    rows, cols = basin_arr.shape
    sink_num = sink_idxs.shape[0]
    func = dll.find_attached_basin_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(sink_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_uint8

    result = func(sink_idxs, sink_num, re_dir_arr, elv_arr, basin_arr, rows, cols)
    if result == 0:
        raise RuntimeError("Can't attach sink region into a coded basin.")

    return int(result)


def region_decompose_uint8(sink_idxs, sink_areas, re_dir_arr, elv_arr, basin_arr):
    rows, cols = basin_arr.shape
    sink_num = sink_idxs.shape[0]
    func = dll.region_decompose_uint8_2

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(sink_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, shape=(sink_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_uint8
    result = func(sink_idxs, sink_areas, sink_num, re_dir_arr, elv_arr, basin_arr, rows, cols)
    return int(result)


def sink_region(sink_idxs, sink_areas, dir_arr):
    rows, cols = dir_arr.shape
    sink_num = sink_idxs.shape[0]
    func = dll.sink_region

    region_flag = np.zeros((sink_num + 1,), dtype=np.int32)

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(sink_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, shape=(sink_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, shape=(sink_num + 1,), flags='C_CONTIGUOUS')]
    func.restype = ctypes.c_int32

    result = func(sink_idxs, sink_areas, sink_num, dir_arr, rows, cols, region_flag)
    return region_flag, int(result)


def sink_merge_uint16(idx_arr, re_dir_arr, elv_arr, basin_arr):
    """
    Integrate uncoded sinks (whose number is larger than 255) into coded basins.
    :param idx_arr: array location indexes of sink bottoms
    :param re_dir_arr: reverse flow direction array
    :param elv_arr: elevation array
    :param basin_arr: sub basins labelled array
    :return:
    """
    sink_num = idx_arr.shape[0]
    if sink_num <= 0:
        return -1

    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.dissolve_sinks_uint16

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint16, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(sink_num,), flags='C_CONTIGUOUS'),
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
    sink_num = idx_arr.shape[0]
    if sink_num <= 0:
        return -1

    rows, cols = basin_arr.shape
    compress_rate = 0.03
    func = dll.dissolve_sinks_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(sink_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_uint8, ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
    func.restype = ctypes.c_int32

    res = func(basin_arr, re_dir_arr, elv_arr, idx_arr, sink_num, rows, cols, compress_rate)

    return res


def pfafstetter(outlet_idx, inlet_idx, threshold, re_dir_arr, upa_arr, basin_arr, sub_outlets, sub_inlets):
    """
    Divide an outflow basin into several (up to 9) sub basins.
    :param outlet_idx: array location indexes of the basin outlet
    :param inlet_idx:
    :param threshold: minimum river threshold
    :param re_dir_arr: reverse flow direction array
    :param upa_arr: up catchment area array
    :param basin_arr: sub basins labelled array
    :param sub_outlets: array location indexes of sub basin outlets
    :param sub_inlets: array location indexes of sub basin outlets
    :return:
    """

    rows, cols = re_dir_arr.shape
    func = dll.pfafstetter_uint8
    outlet_1D = outlet_idx[0] * cols + outlet_idx[1]
    inlet_1D = inlet_idx[0] * cols + inlet_idx[1]

    func.argtypes = [ctypes.c_uint64, ctypes.c_uint64,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_float, ctypes.c_int32, ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(11, 2), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(11, 2), flags='C_CONTIGUOUS')]
    func.restype = ctypes.c_int32

    sub_num = func(outlet_1D, inlet_1D, re_dir_arr, upa_arr, basin_arr, threshold, rows, cols, sub_outlets, sub_inlets)

    return int(sub_num)


def decompose(outlet_idx, inlet_idx, area, decompose_num, dir_arr, re_dir_arr, upa_arr, basin_arr, sub_outlets,
              sub_inlets):
    rows, cols = re_dir_arr.shape
    func = dll.decompose_uint8
    outlet_1D = outlet_idx[0] * cols + outlet_idx[1]
    inlet_1D = inlet_idx[0] * cols + inlet_idx[1]

    func.argtypes = [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_float, ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(11, 2), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(11, 2), flags='C_CONTIGUOUS')]
    func.restype = ctypes.c_int32

    result = func(outlet_1D, inlet_1D, area, decompose_num, dir_arr, re_dir_arr, upa_arr, basin_arr,
                  rows, cols, sub_outlets, sub_inlets)

    return int(result)


def get_basin_envelopes(basin_arr, envelopes):
    """
    Calculate the minimum bounding rectangle for each basin
    :param basin_arr: value range [1, 10], and 0 means no-data
    :param envelopes: result array
    :return:
    """
    rows, cols = basin_arr.shape
    func = dll.get_basin_envelope_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=envelopes.shape, flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32
    func(basin_arr, envelopes, rows, cols)

    return 1


def get_basin_envelopes_int32(basin_arr, envelopes):

    rows, cols = basin_arr.shape
    func = dll.get_basin_envelope_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=envelopes.shape, flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32
    func(basin_arr, envelopes, rows, cols)

    return 1


def island_paint_uint8(iSamples, iColors, dir_arr, re_dir_arr, basin_arr):
    rows, cols = basin_arr.shape
    idx_num = iSamples.shape[0]
    func = dll.island_paint_uint8

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    result = func(iSamples, iColors, idx_num, dir_arr, re_dir_arr, basin_arr, rows, cols)
    return result


def island_paint_int32(iSamples, iColors, dir_arr, re_dir_arr, basin_arr):
    rows, cols = basin_arr.shape
    idx_num = iSamples.shape[0]
    func = dll.island_paint_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    result = func(iSamples, iColors, idx_num, dir_arr, re_dir_arr, basin_arr, rows, cols)
    return result


def island_statistic(island_label, island_num, dir_arr, upa_arr):
    """
    Count the attributes of each island
    :param island_label: island labeled array
    :param island_num: total labeled island num
    :param dir_arr: d8 flow direction numpy array
    :param upa_arr: up catchment area array
    :return:
    """

    island_area = np.zeros(shape=(island_num + 1,), dtype=np.float64)
    island_envelope = np.zeros(shape=(island_num + 1, 4), dtype=np.int32)
    if island_num <= 0:
        return island_area, island_envelope

    rows, cols = upa_arr.shape
    island_envelope[:, 0] = rows
    island_envelope[:, 1] = cols
    func = dll.island_statistic_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, shape=(island_num + 1,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(island_num + 1, 4), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    func(island_label, island_num, island_area, island_envelope, dir_arr, upa_arr, rows, cols)

    return island_area, island_envelope


def calc_coastal_basin_area(basin_arr, basin_num, upa_arr):

    basin_area = np.zeros(shape=(basin_num + 1,), dtype=np.float64)
    if basin_num <= 0:
        return basin_area

    rows, cols = basin_arr.shape
    func = dll.get_basin_area

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, shape=(basin_num + 1,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32
    func(basin_arr, basin_area, upa_arr, rows, cols)

    return basin_area


def calc_coastal_edge(iSamples, iColors, dir_arr, basin_arr):

    rows, cols = basin_arr.shape
    idx_num = iSamples.shape[0]
    func = dll.get_coastal_line

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.uint64, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=1, shape=(idx_num,), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    result = func(iSamples, iColors, idx_num, dir_arr, basin_arr, rows, cols)
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

    func(lake_arr, dir_arr, re_dir_arr, upa_arr, river_ths, rows, cols)


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

    func(lake_arr, max_lake_id, dir_arr, re_dir_arr, upa_arr, river_ths, rows, cols)


def paint_lake_hillslope_int32_c(lake_arr, max_lake_id, re_dir_arr, upa_arr, river_ths):
    """
    not recommended.
    :param lake_arr:
    :param max_lake_id:
    :param re_dir_arr:
    :param upa_arr:
    :param river_ths:
    :return:
    """
    rows, cols = lake_arr.shape
    func = dll.paint_lake_hillslope_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_float, ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    func(lake_arr, max_lake_id, re_dir_arr, upa_arr, river_ths, rows, cols)


def paint_lake_hillslope_new_int32_c(lake_arr, lake_num, dir_arr, re_dir_arr, upa_arr, river_ths):
    rows, cols = lake_arr.shape
    func = dll.paint_lake_hillslope_new_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_float, ctypes.c_int32, ctypes.c_int32, ctypes.POINTER(ctypes.c_int32)]
    func.restype = ctypes.POINTER(ctypes.c_int32)

    basin_num_ptr = ctypes.pointer(ctypes.c_int32(0))
    ptr = func(lake_arr, lake_num, dir_arr, re_dir_arr, upa_arr, river_ths, rows, cols, basin_num_ptr)

    basin_num = basin_num_ptr.contents.value
    arr_type = ctypes.c_int32 * (2 * (basin_num + 1))
    address = ctypes.addressof(ptr.contents)
    outlets = np.frombuffer(arr_type.from_address(address), dtype=np.int32)
    outlets = outlets.reshape((-1, 2))

    return outlets, basin_num


def paint_lake_local_catchment_int32_c(lake_arr, max_lake_id, re_dir_arr):
    """

    :param lake_arr:
    :param max_lake_id:
    :param re_dir_arr:
    :return:
    """
    rows, cols = lake_arr.shape
    func = dll.paint_lake_local_catchment_int32

    func.argtypes = [np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    func(lake_arr, max_lake_id, re_dir_arr, rows, cols)


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
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, shape=(lake_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.POINTER(ctypes.c_int32)

    block_arr = np.zeros(shape=(lake_num,), dtype=np.int32)
    ptr = func(lake_arr, lake_num, block_arr, dir_arr, rows, cols)

    arr_type = ctypes.c_int32 * block_arr[-1]
    address = ctypes.addressof(ptr.contents)
    down_lake_arr = np.frombuffer(arr_type.from_address(address), dtype=np.int32)

    return down_lake_arr, block_arr


def create_route_between_lake_c(lake_arr, lake_num, dir_arr, upa_arr):
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


def check_outlet_on_mainstream(outlet_ridx, outlet_cidx, inlet_ridx, inlet_cidx, inlet_dir, dir_arr):
    """

    :param outlet_ridx:
    :param outlet_cidx:
    :param inlet_ridx:
    :param inlet_cidx:
    :param inlet_dir:
    :param dir_arr:
    :return:
    """
    rows, cols = dir_arr.shape
    func = dll.check_on_mainstream

    func.argtypes = [ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_uint8,
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows, cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32]
    func.restype = ctypes.c_int32
    flag = func(outlet_ridx, outlet_cidx, inlet_ridx, inlet_cidx, inlet_dir, dir_arr, cols)
    return flag