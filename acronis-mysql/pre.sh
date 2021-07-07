#!/bin/bash

MY_DATABASE="postone"
DST_DIR="/var/tmp/mysql_backup"

for TABLE in $(mysql -N -B -e "show tables from $MY_DATABASE");
do
    echo "Backing up $TABLE"
    mysqldump $MY_DATABASE "$TABLE" > $DST_DIR/"$TABLE".sql
done;