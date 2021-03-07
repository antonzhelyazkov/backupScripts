import getopt
import socket
import sys

ARGV = sys.argv[1:]
VERBOSE = False
CONFIG_FILE = "./pg_backup.json"
LOG_DIR_DEFAULT = "."
HOSTNAME = socket.gethostname().split(".")[0]

try:
    opts, argv = getopt.getopt(ARGV, "c:v", ["config=", "verbose"])
except getopt.GetoptError as err:
    print(err)
    opts = []

for opt, arg in opts:
    if opt in ['-c', '--config']:
        CONFIG_FILE = arg
    if opt in ['-v', '--verbose']:
        VERBOSE = True

