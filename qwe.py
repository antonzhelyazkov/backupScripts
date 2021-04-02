import os
import tarfile

dir = "/opt/neterra-cdn-nodejs/"

with tarfile.open('new_archive.tar.gz', 'w') as archive:
    for i in os.listdir(dir):
        archive.add(i, filter=lambda x: x if x.name.endswith('.txt') else None)
    archive.list()