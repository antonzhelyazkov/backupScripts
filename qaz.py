import os
import tarfile

dir_q: str = "/usr/local/neterratv-scripts/"
excludes = ["v2wm", "wm-py", "delete"]


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
    # if any(qwer in asd.name for qwer in excludes):
    #     return None
    # else:

    print(type(asd))

    return asd


all_f = walk_files(dir_q)

with tarfile.open('new_archive.tar.gz', 'w') as archive:
    for i in all_f:
        archive.add(i, filter=ads(i))
    archive.list()
