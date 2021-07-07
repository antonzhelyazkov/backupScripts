#!/bin/bash

MY_DATABASE="postone"
DST_DIR="/var/tmp/mysql_backup"
DST_DIR_TABLES=$DST_DIR"/"$MY_DATABASE
LOG_FILE="/var/log/acronis_pre.log"

echo "$(date +'%Y/%m/%d %H:%M:%S')" "START" >> $LOG_FILE
mkdir -p "$DST_DIR_TABLES"

for TABLE in $(mysql -N -B -e "show tables from $MY_DATABASE");
do
    echo "$(date +'%Y/%m/%d %H:%M:%S')" "Backing up $TABLE" >> $LOG_FILE
    mysqldump $MY_DATABASE "$TABLE" | pigz > $DST_DIR_TABLES/"$TABLE".sql.gz
done;

echo "$(date +'%Y/%m/%d %H:%M:%S')" "Backing up database $MY_DATABASE" >> $LOG_FILE
mysqldump -B $MY_DATABASE | pigz > $DST_DIR"/"$MY_DATABASE.sql.gz
echo "$(date +'%Y/%m/%d %H:%M:%S')" "FINISH" >> $LOG_FILE