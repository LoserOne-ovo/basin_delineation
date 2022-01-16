import os


def get_basin_folder(root_folder, basin_code):
    """

    :param root_folder:
    :param basin_code:
    :return:
    """
    work_folder = root_folder
    for c in basin_code:
        work_folder = os.path.join(work_folder, c)

    return work_folder
