#!/usr/bin/env bash

DST_DIR="/var/tmp/mysql_backup"
rm -rf "${DST_DIR:?}/"*
rm -f "/tmp/acronis_mysql.lock"
