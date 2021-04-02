import os
import tarfile
from pathlib import Path

dir_q: str = "/usr/local/neterratv-scripts/"
excludes = ["v2wm", "wm-py"]


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


def ads(asd):
    print(f"qweqwe {asd}")


all_f = walk_files(dir_q)

with tarfile.open('new_archive.tar.gz', 'w') as archive:
    for i in all_f:
        archive.add(i, filter=ads)
#    archive.list()
