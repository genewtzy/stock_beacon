import json
import os


# 读取JSON文件


def read_json_file(file_path):
    """

    :param file_path:
    :return:
    """
    if not os.path.exists(file_path) or (os.stat(file_path).st_size == 0):
        return None
    with open(file_path, encoding='utf-8') as file:
        data = json.load(file)
    return data


# 写入JSON文件
def write_json_file(file_path, data):
    """

    :param file_path:
    :param data:
    """
    try:
        os.remove(file_path)
    except OSError as e:
        print('remove', file_path, str(e))
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
