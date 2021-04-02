import os
import tarfile
from pathlib import Path

dir_q: str = "/usr/local/neterratv-scripts/"
excludes = ["v2wm"]


# with tarfile.open('new_archive.tar.gz', 'w') as archive:
#     for i in os.listdir(dir):
#         archive.add(i, filter=lambda x: x if x.name.endswith('.txt') else None)
#     archive.list()

def walk_files(directory: str) -> list:
    all_files = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isdir(full_path):
            all_files.extend(walk_files(full_path))
        else:
            all_files.append(full_path)

    return all_files


def remove_excludes(file_list: list, excludes_list: list) -> list:
    for element in file_list:
        for exclude in excludes_list:
            if exclude in element:
                print(element)
                file_list.remove(element)
                print(len(file_list))

    return file_list


all_f = walk_files(dir_q)
filtered_f = remove_excludes(all_f, excludes)
# print(all_f)
print(len(all_f))
print(len(filtered_f))

with tarfile.open('new_archive.tar.gz', 'w') as archive:
    for i in filtered_f:
        archive.add(i)
#    archive.list()
