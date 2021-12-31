import os
import shutil


def clone_basin(folder, code, sub_folder, sub_code):


    # clone shp
    file1 = os.path.join(folder, code + '.shp')
    file2 = os.path.join(folder, code + '.shx')
    file3 = os.path.join(folder, code + '.dbf')
    file4 = os.path.join(folder, code + '.prj')

    if os.path.exists(file1) & os.path.exists(file2) & \
            os.path.exists(file3) & os.path.exists(file4):
        shutil.copy2(file1, os.path.join(sub_folder, sub_code + '.shp'))
        shutil.copy2(file2, os.path.join(sub_folder, sub_code + '.shx'))
        shutil.copy2(file3, os.path.join(sub_folder, sub_code + '.dbf'))
        shutil.copy2(file4, os.path.join(sub_folder, sub_code + '.prj'))
    else:
        raise IOError("missing shapefile in path %s!" % folder)

    # clone tif
    dir_tif = os.path.join(folder, code + '_dir.tif')
    upa_tif = os.path.join(folder, code + '_dir.tif')
    elv_tif = os.path.join(folder, code + '_dir.tif')
    if os.path.exists(dir_tif) & os.path.exists(upa_tif) & \
            os.path.exists(elv_tif):
        shutil.copy2(dir_tif, os.path.join(sub_folder, sub_code + '_dir.tif'))
        shutil.copy2(upa_tif, os.path.join(sub_folder, sub_code + '_upa.tif'))
        shutil.copy2(elv_tif, os.path.join(sub_folder, sub_code + '_elv.tif'))
    else:
        raise IOError("missing .tif file in path %s!" % folder)

    # clone sqlite3 db
    db_path = os.path.join(folder, code + '.db')
    if os.path.exists(db_path):
        shutil.copy2(db_path, os.path.join(sub_folder, sub_code + '.db'))
    else:
        raise IOError("missing .db file in path %s!" % folder)

    return 1


def get_basin_folder(root_folder, basin_code):
    work_folder = root_folder
    for c in basin_code:
        work_folder = os.path.join(work_folder, c)

    return work_folder


def get_basin_db(root_folder, basin_code):
    basin_folder = get_basin_folder(root_folder, basin_code)
    basin_db = os.path.join(basin_folder, basin_code + ".db")

    return basin_db


def clone_shp(folder, code, sub_folder, sub_code):
    """
    复制流域范围的shp文件到下一层级
    :param folder:
    :param code:
    :param sub_folder:
    :param sub_code:
    :return:
    """
    file1 = os.path.join(folder, code + '.shp')
    file2 = os.path.join(folder, code + '.shx')
    file3 = os.path.join(folder, code + '.dbf')
    file4 = os.path.join(folder, code + '.prj')

    if os.path.exists(file1) & os.path.exists(file2) & \
            os.path.exists(file3) & os.path.exists(file4):
        shutil.copy2(file1, os.path.join(sub_folder, sub_code + '.shp'))
        shutil.copy2(file2, os.path.join(sub_folder, sub_code + '.shx'))
        shutil.copy2(file3, os.path.join(sub_folder, sub_code + '.dbf'))
        shutil.copy2(file4, os.path.join(sub_folder, sub_code + '.prj'))
    else:
        raise IOError("missing shapefile in path %s!" % folder)


def copy_not_divided_basin(root_folder, code, sink_num):
    work_folder = root_folder
    for c in code:
        work_folder = os.path.join(work_folder, c)
    target_folder = os.path.join(work_folder, '0')
    new_code = code + '0'
    if not os.path.exists(target_folder):
        os.mkdir(target_folder)

    # 复制tif文件
    src_dir = os.path.join(work_folder, code + '_dir.tif')
    src_upa = os.path.join(work_folder, code + '_upa.tif')
    tgt_dir = os.path.join(target_folder, new_code + '_dir.tif')
    tgt_upa = os.path.join(target_folder, new_code + '_upa.tif')
    if os.path.exists(src_dir):
        shutil.copy2(src_dir, tgt_dir)
    else:
        raise IOError("Could not find input file %s!" % src_dir)
    if os.path.exists(src_upa):
        shutil.copy2(src_upa, tgt_upa)
    else:
        raise IOError("Could not find input file %s!" % src_upa)

    if sink_num > 1:
        src_elv = os.path.join(work_folder, code + '_elv.tif')
        tgt_elv = os.path.join(target_folder, new_code + '_elv.tif')
        if os.path.exists(src_elv):
            shutil.copy2(src_elv, tgt_elv)
        else:
            raise IOError("Could not find input file %s!" % src_elv)

    # 复制数据库文件
    src_db = os.path.join(work_folder, code + '.db')
    tgt_db = os.path.join(target_folder, new_code + '.db')
    shutil.copy2(src_db, tgt_db)
    # 复制shp文件
    clone_shp(work_folder, code, target_folder, new_code)


def copy_indivisible_basin(root_folder, code):
    work_folder = root_folder
    for c in code:
        work_folder = os.path.join(work_folder, c)

    target_folder = os.path.join(work_folder, '0')
    if not os.path.exists(target_folder):
        os.mkdir(target_folder)
    new_code = code + '0'

    clone_shp(work_folder, code, target_folder, new_code)
