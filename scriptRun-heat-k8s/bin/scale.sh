#!/bin/bash
# scale rc num
usage(){
   echo "$0  stackname rc-name rc-num"
   echo "e.g. $0  config-center java 2"
}

if [ $# != 3 ]; then
    usage  && exit 
fi

stackname=$1
rcname=$2
rc=`kubectl get rc --namespace=$stackname  | grep $rcname | awk '{print $1}' | sort |  sed -n '1,3p'`
echo $rc
if [ "$rc" = "" ];then
    echo "rc not found." &&  exit 
fi

#kubectl scale rc $rc  --replicas=$3 --namespace=$stackname

