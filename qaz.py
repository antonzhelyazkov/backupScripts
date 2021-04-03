import os
import tarfile

dir_q: str = "/opt/neterra-cdn-nodejs/modules/cdn-video-appender/"
excludes = ["cdn-video-appender", "opt/neterra-cdn-nodejs/modules/cdn-video-appender/node_modules/", "node_modules"]


def walk_files(directory: str) -> list:
    all_files = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isdir(full_path):
            all_files.extend(walk_files(full_path))
        else:
            all_files.append(full_path)

    return all_files


def excl(file_to_check):
    if any(item_file in file_to_check.name for item_file in excludes):
        return None
    else:
        return file_to_check


all_f = walk_files(dir_q)

with tarfile.open('new_archive.tar.gz', 'w:gz') as archive:
    for file in all_f:
        archive.add(file)
    archive.list()
