import os
import tarfile
from pathlib import Path

dir_q: str = "/opt/neterra-cdn-nodejs/"


# with tarfile.open('new_archive.tar.gz', 'w') as archive:
#     for i in os.listdir(dir):
#         archive.add(i, filter=lambda x: x if x.name.endswith('.txt') else None)
#     archive.list()

def walk_files(directory: str):
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isdir(full_path):
            walk_files(full_path)
        else:
            print(full_path)



