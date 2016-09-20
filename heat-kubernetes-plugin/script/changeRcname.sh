#!/bin/bash 
#add random to rcname

usage(){
    echo "$0  heat_jsonname rcname1 rcname2 ..."
    echo "e.g. $0 heat_xxx.json  java-1 java-2"
}

arglist=$@
basedir=$( cd ` dirname $0 ` && cd ..&& pwd )
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

basedir2=$( cd ` dirname $0 ` && pwd )

echo "force_change_list === [ $rcnamelist ]"
echo "force_change_json=== [ $jsonfile ]"
python $basedir2/changeRC.py  $jsonfile $rcnamelist


