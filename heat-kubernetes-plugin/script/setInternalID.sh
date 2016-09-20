#!/bin/bash 

usage(){
    echo "$0  heat_jsonfile last_heat_jsonfile"
    echo "e.g. $0 heat_dev_avery.json  last_heat_dev_avery.json"
}

basedir=$( cd ` dirname $0 ` && cd ..&& pwd )
if [ $# -lt 2 ];then
  usage
  exit 0
fi

if [ $2 = "@" ]
  then 
    echo "create new stack."
    exit 0
fi
   
new_jsonfile=$basedir/$1
last_jsonfile=$basedir/$2

basedir2=$( cd ` dirname $0 ` && pwd )
echo "newjson  === [ $new_jsonfile ]"
echo "lastjson === [ $last_jsonfile ]"
python $basedir2/setLastTimeinternalID.py  $new_jsonfile $last_jsonfile


