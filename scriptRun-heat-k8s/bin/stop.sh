#!/bin/bash
# stop stack
usage(){
   echo "$0   stackname"
   echo "e.g. $0  "
}

if [ $# != 1 ]; then
    usage  && exit 
fi


stackname=$1
#run rc 
 check=`heat stack-list | grep $stackname`
 if [ "$check" != "" ]; then 
     heat stack-delete $stackname >> /tmp/heat-client.log
    echo "delete resource $stackname"
    for i in $(seq 1 15)
        do 
            res=`heat stack-list | grep $stackname` 
            if [ "$res" != "" ]; then
                printf ". "
                sleep 1 
            fi
        done
     echo "done"
 fi   

