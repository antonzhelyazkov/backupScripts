#!/bin/bash

MY_DATABASE="postone"
DST_DIR="/var/tmp/mysql_backup"
DST_DIR_TABLES=$DST_DIR"/"$MY_DATABASE

echo $DST_DIR_TABLES

#for TABLE in $(mysql -N -B -e "show tables from $MY_DATABASE");
#do
#    echo "Backing up $TABLE"
#    mysqldump $MY_DATABASE "$TABLE" > $DST_DIR/"$TABLE".sql
#done;
