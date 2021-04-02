import os
import tarfile
from pathlib import Path

dir_q: str = "/opt/neterra-cdn-nodejs/"


# with tarfile.open('new_archive.tar.gz', 'w') as archive:
#     for i in os.listdir(dir):
#         archive.add(i, filter=lambda x: x if x.name.endswith('.txt') else None)
#     archive.list()

# def walk_files(directory: str):
#     for item in os.listdir(directory):
#         if os.path.isdir(item):
#             walk_files(item)
#         else:
#             print(item)


for path in os.listdir(dir_q):
    full_path = os.path.join(dir_q, path)
    if os.path.isfile(full_path):
        print(full_path)
