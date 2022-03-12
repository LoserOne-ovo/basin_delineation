import numpy as np
import ctypes
import platform


if platform.system() == "Windows":
    dll = ctypes.WinDLL("lake.dll")
elif platform.system() == "Linux":
    dll = ctypes.CDLL("lake.so.64")
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
                     ctypes.c_int, ctypes.c_int]
    func.restype = ctypes.POINTER(ctypes.c_ubyte)
    ptr = func(dir_arr, rows, cols)

    arr_type = ctypes.c_ubyte * (rows * cols)
    address = ctypes.addressof(ptr.contents)
    result = np.frombuffer(arr_type.from_address(address), dtype=np.uint8)
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
    func = dll.correct_lake_network

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