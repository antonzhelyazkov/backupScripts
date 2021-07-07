#!/bin/bash

MY_DATABASE="postone"
DST_DIR="/var/tmp/mysql_backup"
DST_DIR_TABLES=$DST_DIR"/"$MY_DATABASE

mkdir -p "$DST_DIR_TABLES"

for TABLE in $(mysql -N -B -e "show tables from $MY_DATABASE");
do
    echo "Backing up $TABLE"
    mysqldump $MY_DATABASE "$TABLE" | pigz > $DST_DIR_TABLES/"$TABLE".sql.gz
done;

mysqldump -B $MY_DATABASE | pigz > $DST_DIR"/"$MY_DATABASE.sql.gz