#!/bin/bash

OPTS=$(getopt -o vc: --long verbose,config: -n 'parse-options' -- "$@")
getOptsExitCode=$?
if [ $getOptsExitCode != 0 ]; then
	echo "Failed parsing options." >&2 ;
	exit 1 ;
fi

eval set -- "$OPTS"

localCopy=1
localCopyPath="/var/tmp"
localCopyDays=1
localBackupDays=$(date +%Y%m%d%H%M -d "$localCopyDays day ago")
verbose=0
yearCopy=0
HELP=false
mongoBin="/usr/bin/mongo"

while true; do
	case "$1" in
		-c | --config ) cinfigFile="$2"; shift ;;
		-v | --verbose ) verbose=1; shift ;;
		-h | --help ) HELP=true; shift ;;
		-l | --local-copy ) localCopy=1; shift ;; 
		-y | --year-copy ) yearCopy=1; shift ;;
		-- ) shift; break ;;
		* ) break ;;
	esac
done


function logPrint() {
logMessage=$1
if [ -z $2 ]; then
        nagios=0
else
        if [[  $2 =~ ^[0-1]{1}$ ]]; then
                nagios=$2
        else
                nagios=0
        fi
fi

if [ -z $3 ]; then
        exitCommand=0
else
        if [[  $3 =~ ^[0-1]{1}$ ]]; then
                exitCommand=$3
        else
                exitCommand=0
        fi
fi

echo $(date) $logMessage >> $scriptLog

if [ $verbose -eq 1 ]; then
        echo $logMessage
fi

if [ $nagios -eq 1 ]; then
        echo $logMessage >> $nagiosLog
fi

if [ $exitCommand -eq 1 ]; then
        exit
fi
}
