import os
import shutil
import time


def copy_tif_by_rectangle(dl_lat, dl_lon, ur_lat, ur_lon, suffix, src_folder, tgt_folder):
    """
    栅格数据是按 5°×5° 分幅。分幅文件名称是左下角的经纬度。
    函数目标，将矩形范围内的栅格文件，复制到目标的文件夹内。
    :param dl_lat: 左下角的纬度（5的倍数，负数表示南纬）
    :param dl_lon: 左下角的经度（5的倍数，负数表示西经）
    :param ur_lat: 右上角的纬度（5的倍数，负数表示南纬）
    :param ur_lon: 右上角的经度（5的倍数，负数表示西经）
    :param suffix: 1 = "_dir", 2 = "_upa", 3 = "_elv"
    :param src_folder: 原始数据所在文件夹
    :param tgt_folder: 目标文件夹
    :return:
    """

    time_begin = time.time()
    print('begin at:  ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_begin)))

    # 检查文件夹路径是否存在
    if not os.path.exists(src_folder):
        raise IOError("Source folder : %s does not exist!" % src_folder)
    if not os.path.exists(tgt_folder):
        os.makedirs(tgt_folder)
    os.chdir(src_folder)

    if suffix == 1:
        suf_name = "_dir.tif"
    elif suffix == 2:
        suf_name = "_upa.tif"
    elif suffix == 3:
        suf_name = "_elv.tif"
    else:
        raise RuntimeError("Argument suffix should be one of [1, 2, 3]!")

    # 循环复制
    for i in range(dl_lat, ur_lat, 5):
        for j in range(dl_lon, ur_lon, 5):
            # 纬度
            if i < 0:
                lat = 's' + '{:0>2d}'.format(abs(i))
            else:
                lat = 'n' + '{:0>2d}'.format(i)
            # 经度
            if j < 0:
                lon = 'w' + '{:0>3d}'.format(abs(j))
            else:
                lon = 'e' + '{:0>3d}'.format(j)
            # 完整文件名
            file_name = lat + lon + suf_name
            if os.path.isfile(file_name):
                shutil.copy(file_name, target_folder)

    time_finish = time.time()
    print('finish at:  ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_finish)))
    print('Output consume:  ' + '{:.4f}'.format(time_finish - time_begin) + 's')
    print('done!')


if __name__ == '__main__':

    down_left_lat = 0
    down_left_lon = 55
    up_right_lat = 60
    up_right_lon = 155

    source_folder = r"H:\90mDEM\Adjusted_Elevation\data"
    target_folder = r"F:\demo\Asia\data_prepare\source\elv"

    copy_tif_by_rectangle(down_left_lat, down_left_lon, up_right_lat, up_right_lon, 1, source_folder, target_folder)
    copy_tif_by_rectangle(down_left_lat, down_left_lon, up_right_lat, up_right_lon, 2, source_folder, target_folder)
    copy_tif_by_rectangle(down_left_lat, down_left_lon, up_right_lat, up_right_lon, 3, source_folder, target_folder)