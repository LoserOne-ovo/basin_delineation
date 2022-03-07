import numpy as np
import ctypes
import platform


if platform.system() == "Windows":
    dll = ctypes.WinDLL("ws_dln106.dll")
elif platform.system() == "Linux":
    dll = ctypes.CDLL("ws_dln106.so.64")
else:
    raise RuntimeError("Unsupported platform %s" % platform.system())


def calc_reverse_dir(dir_arr):
    """
    Call C dll to calculate the reverse d8 flow direction
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


def get_basin_envelopes(basin_arr, basin_envelopes):
    """

    :param basin_arr: value range [1, 10], and 0 means no-data
    :param basin_envelopes:
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

    :param island_label:
    :param island_num:
    :param island_paint_flag:
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


def paint_up_mosaiced_uint8(idx_arr, re_dir_arr, basin_arr):

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


def sink_merge_uint16(idx_arr, re_dir_arr, elv_arr, basin_arr):

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


def paint_up_uint8(idx_arr, colors, re_dir_arr, basin_arr):

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


def island_statistic(island_label, island_num, dir_arr, upa_arr):
    """

    :param island_label:
    :param island_num:
    :param dir_arr:
    :param upa_arr:
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
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, shape=(island_num,), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, shape=(island_num,4), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, shape=(rows,cols), flags='C_CONTIGUOUS'),
                     ctypes.c_int32, ctypes.c_int32]
    func.restype = ctypes.c_int32

    island_sample = np.zeros(shape=(island_num, 2), dtype=np.int32)
    island_center = np.zeros(shape=(island_num, 2), dtype=np.float32)
    island_radius = np.zeros(shape=(island_num, ), dtype=np.float32)
    island_area = np.zeros(shape=(island_num,), dtype=np.float32)
    island_ref_area = np.zeros(shape=(island_num,), dtype=np.float32)
    island_envelope = np.zeros(shape=(island_num, 4), dtype=np.int32)
    island_envelope[:, 0] = rows
    island_envelope[:, 1] = cols

    func(island_label, island_num, island_center, island_sample, island_radius, island_area, island_ref_area,
         island_envelope, dir_arr, upa_arr, rows, cols)

    return island_center, island_sample, island_radius, island_area, island_ref_area, island_envelope








