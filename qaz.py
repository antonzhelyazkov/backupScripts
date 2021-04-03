import os
import tarfile
from pathlib import Path

dir_q: str = "/opt/neterra-cdn-nodejs/modules/cdn-video-appender"
excludes = ["v2wm", "wm-py", "cdn-video-appender/node_modules"]


def walk_files(directory: str) -> list:
    all_files = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isdir(full_path):
            all_files.extend(walk_files(full_path))
        else:
            all_files.append(full_path)

    return all_files


def exclude_function(asd):
    if any(qwer in asd.name for qwer in excludes):
        return None
    else:
        return asd


all_f = walk_files(dir_q)

with tarfile.open('new_archive.tar.gz', 'w') as archive:
    for iqq in all_f:
        archive.add(iqq, filter=exclude_function(iqq))
    archive.list()
