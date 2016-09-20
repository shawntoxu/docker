#!/bin/bash
#set -x 
usage(){
    echo "$0  sys-shortname"
    echo "e.g. $0 c"
}

if [ $# != 1 ]; then
      usage && exit
fi

getImage() {
  podname=`kubectl get pod --namespace=$1 |  awk '{print $1}' | sort |  sed -n '2p'`
  images=`kubectl describe pod $podname  --namespace=$1 | grep Image\(s\) |  awk '{print $2}'` 
}

getContainerInfo() {
 pods=`kubectl get pod --namespace=$stackname | grep $sysname| awk '{print $1}' | sort |  sed -n '1,3p'`
 innerIP=""
 if [ "$pods" != "" ]; then
  for i in $pods
      do 
        if [ "$i" != "NAME" ]; then
          thisIP=`kubectl describe pod $i --namespace=$stackname | grep IP: | awk '{print $2}'`
          innerIP+=" "$thisIP
        fi
     done
 
  if [ "$innerIP" != "" ]; then  
    echo "$sysname系统内部ip:"$innerIP
  fi
  port=`kubectl get service --namespace="$stackname" | awk '{print $5}' | grep TCP | awk -F "/" '{print $1}'`
  echo -e "\e[1;31m外部访问地址:10.7.0.3:$port \e[0m"
  getImage  "$stackname"
  echo "镜像版本:"$images
  echo "---------------------------------------------------------------------------------"
fi 
}

#username=`whoami`
if [ "$1" = "c" ]; then
    sysname="content"
elif [ "$1" = "p" ]; then
    sysname="payment"
elif [ "$1" = "a" ]; then
    sysname="adspush"
elif [ "$1" = "s" ]; then
    sysname="statistics"
elif [ "$1" = "all" ]; then
    sysname="gkt"
else
   echo "没有匹配到相应系统." && exit    
fi

if [ $sysname != "gkt" ]; then
 stackname="gkt-$sysname"
 check=`heat stack-list | grep $stackname`
 if [ "$check" != "" ]; then 
    getContainerInfo
 fi
else
 for sys in resin
 do
      stackname="vn-resin"
      check=`heat stack-list | grep $stackname`
      if [ "$check" != "" ]; then 
       sysname=$sys
       getContainerInfo 
      fi
 done
fi

