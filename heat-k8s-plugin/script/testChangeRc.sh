#!/bin/bash

arglist=$@
basedir=$( cd ` dirname $0 ` && pwd )
if [ $# -lt 2 ];then
  echo " no input rc name"
  exit 0
fi
jsonfile=$basedir/$1
rcnamelist=""
for i in $arglist
  do
    result=$(echo $i | grep json)
    if [[ "$result" == "" ]]
     then
	rcnamelist=$rcnamelist" "$i
    fi
  done

echo $jsonfile
echo $rcnamelist

python changeRC.py xxxx.json java-1 php-2

