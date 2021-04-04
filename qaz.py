import ftplib
import getopt
import json
import sys

CONFIG_FILE = "./config.json"
argv = sys.argv[1:]

try:
    opts, argv = getopt.getopt(argv, "c:v", ["config=", "verbose"])
except getopt.GetoptError as err:
    print(err)
    opts = []

for opt, arg in opts:
    if opt in ['-c', '--config']:
        config_file = arg
    if opt in ['-v', '--verbose']:
        VERBOSE = True

config_open = open(CONFIG_FILE, encoding='utf-8')
CONFIG_DATA = json.load(config_open)


def remove_ftp_dir(ftp_sess, path):
    for (name, properties) in ftp_sess.mlsd(path=path):
        if name in ['.', '..']:
            continue
        elif properties['type'] == 'file':
            ftp_sess.delete(f"{path}/{name}")
        elif properties['type'] == 'dir':
            remove_ftp_dir(ftp_sess, f"{path}/{name}")
    ftp_sess.rmd(path)


ftp = ftplib.FTP(CONFIG_DATA['ftp_login']['ftp_host'],
                 CONFIG_DATA['ftp_login']['ftp_user'],
                 CONFIG_DATA['ftp_login']['ftp_pass'])

remove_ftp_dir(ftp, 'origin1.neterra.tv')
