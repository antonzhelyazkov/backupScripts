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

while true; do
	case "$1" in
		-c | --config ) configFile="$2"; shift ;;
		-v | --verbose ) verbose=1; shift ;;
		-h | --help ) HELP=true; shift ;;
		-l | --local-copy ) localCopy=1; shift ;; 
		-y | --year-copy ) yearCopy=1; shift ;;
		-- ) shift; break ;;
		* ) break ;;
	esac
done

dateTs=$(date +%s)
ownScriptName=$(basename "$0" | sed -e 's/.sh$//g')
scriptLog="/var/log/$ownScriptName.log"
nagiosLog="/var/log/$ownScriptName.nagios"
lastRun="/var/log/$ownScriptName.last"

function logPrint() {
logMessage=$1
if [ -z "$2" ]; then
        nagios=0
else
        if [[  $2 =~ ^[0-1]{1}$ ]]; then
                nagios=$2
        else
                nagios=0
        fi
fi

if [ -z "$3" ]; then
        exitCommand=0
else
        if [[  $3 =~ ^[0-1]{1}$ ]]; then
                exitCommand=$3
        else
                exitCommand=0
        fi
fi

# shellcheck disable=SC2046
echo $(date) "$logMessage" >> "$scriptLog"

if [ $verbose -eq 1 ]; then
        echo "$logMessage"
fi

if [ $nagios -eq 1 ]; then
        echo "$logMessage" >> "$nagiosLog"
fi

if [ $exitCommand -eq 1 ]; then
        exit
fi
}

function decodeBase64() {
  val=$(echo "${1}" | base64 --decode | jq -r "${2}")
  echo "$val"
}

function addDirectorySlash(){
  echo "$1" | grep -qE "/$"
  checkSlash=$?
  if [ "$checkSlash" == 0 ]
  then
    echo "$1"
  else
    echo "$1/"
  fi
}

########################################################

logPrint START 0 0

if [ -f "$nagiosLog" ]; then
        logPrint "ERROR file $nagiosLog exists EXIT!" 1 1
else
        echo $$ > "$nagiosLog"
fi

hash jq 2>/dev/null
jqCheck=$?
if [ $jqCheck -ne 0 ]
then
	rm -f "$nagiosLog"
	logPrint "ERROR jq not found!" 1 1
fi

if [ -f "$configFile" ]
then
	logPrint "INFO config file $configFile found" 0 0
else
	rm -f "$nagiosLog"
	logPrint "ERROR config file $configFile not found" 1 1
fi

############ validate JSON ############

validateConfig=$(jq -r type < "$configFile")
if [ "$validateConfig" == "object" ]
then
  logPrint "INFO config file is correct" 0 0
else
  logPrint "ERROR config file $configFile is not correct" 1 1
fi

############ validate JSON ############

############ variables ############

mongoHost=$(jq -r .mongo_host "$configFile")
dstDirString=$(jq -r .dstDirBase "$configFile")
dstDirBase=$(addDirectorySlash "$dstDirString")
serverName=$(jq -r .hostname "$configFile")
ftpRemotePath="/$serverName-mongo-backup/"
# Speed is in bytes per second. 0 - means unlimited
keepRemoteBackupDays=5
remoteBackupDays=$(date +%Y%m%d%H%M -d "$keepRemoteBackupDays day ago")
oneYearAgo=$(date +%Y%m%d%H%M -d "1 year ago")
dateToday=$(date +%d)

mongoDir=$(addDirectorySlash "$dstDirBase$serverName")
currentBackupDir="$mongoDir$(date +%Y%m%d%H%M)"

if [ verbose == 0 ]
then
  mongodumpBin="/usr/bin/mongodump"
else
  mongodumpBin="/usr/bin/mongodump --quiet"
fi

############ variables ############

############ FTP Connect ############

ftpHost=$(jq -r .ftp.ftp_host "$configFile")
ftpUser=$(jq -r .ftp.ftp_user "$configFile")
ftpPass=$(jq -r .ftp.ftp_pass "$configFile")

hash ftp 2>/dev/null
ftpCheck=$?
if [ $ftpCheck -ne 0 ]
then
        rm -f "$nagiosLog"
        logPrint "ERROR ftp not found!" 1 1
fi

echo 'exit' | ftp ftp://"$ftpUser":"$ftpPass"@"$ftpHost"/
checkFTP=$?
if [ $checkFTP -ne 0 ]
then
	logPrint "ERROR Failed to connect to ftp host" 0 1
else
	logPrint "INFO connected to ftp host" 0 0
fi

############ FTP Connect ############

if mkdir -p "$currentBackupDir"
then
  logPrint "INFO directory $currentBackupDir was created" 0 0
else
  logPrint "ERROR in directory create $currentBackupDir" 1 1
fi

tmpArr=$(jq -c .mongo "$configFile")

for row in $(echo "$tmpArr" | jq -r '.[] | @base64')
do
   dbName=$(decodeBase64 "$row" '.db')
   dbUser=$(decodeBase64 "$row" '.user')
   dbPass=$(decodeBase64 "$row" '.pass')
   dumpCommand="$mongodumpBin --host $mongoHost --port 27017 -u $dbUser -p $dbPass --db $dbName --gzip --out $currentBackupDir"
   $dumpCommand
   echo $?
done

########################################################

if grep -Fq "ERROR" "$nagiosLog" ; then
  logPrint "ERRORS are found. Must not remove $nagiosLog" 0 0
else
  rm -f "$nagiosLog"
  logPrint "FINISH" 0 0
fi

echo "$dateTs" > "$lastRun"
