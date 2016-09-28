#!/bin/bash
usage(){
    echo "$0  stackname"
    echo "e.g. $0 config-center"
}

if [ $# != 1 ]; then
      usage && exit
fi

getImage() {
  podname=`kubectl get pod --namespace=$1 |  awk '{print $1}' | sort |  sed -n '1,5p'`
  imagelist=""
  if [ "$podname" != "" ]; then
    for j in $podname
    do
        if [ "$j" != "NAME" ]; then
            thisImage=`kubectl describe pod $j  --namespace=$1 | grep Image\(s\) |  awk '{print $2}'`
            if [[ $imagelist =~ $thisImage ]];then 
                echo "included" >>/tmp/tmp
                #imagelist+="\n$thisImage "
            else
                imagelist+="\n$thisImage "
            fi
        fi
    done
  fi 
  #images=`kubectl describe pod $podname  --namespace=$1 | grep Image\(s\) |  awk '{print $2}'` 
}

getContainerInfo() {
 pods=`kubectl get pod --namespace=$stackname |  awk '{print $1}' | sort |  sed -n '1,5p'`
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
    echo "$stackname 系统内部ip:"$innerIP
  fi
  port=`kubectl get service --namespace="$stackname" | awk '{print $5}' | grep TCP | awk -F "/" '{print $1}'`
  #echo -e "\e[1;31m外部访问地址:10.2.1.15:$port 10.2.1.16:$port \e[0m"
  getImage  "$stackname"
  echo -e "image version :"$imagelist
  echo "---------------------------------------------------------------------------------"
fi 
}

 stackname=$1
 check=`heat stack-list | grep $stackname`
 if [ "$check" != "" ]; then 
    getContainerInfo
 fi

