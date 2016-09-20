#!/bin/bash
#set -x 
usage(){
    echo "$0  stackname"
    echo "e.g. $0 test"
}

if [ $# != 1 ]; then
      usage && exit
fi

stackname=$1

getImage() {
  podname=`kubectl get pod --namespace=$1 |  awk '{print $1}' | sort |  sed -n '2p'`
echo "podname="$podname
  images=`kubectl describe pod $podname  --namespace=$1 | grep Image\(s\) |  awk '{print $2}'` 
echo "images="$images
}

getContainerInfo() {
 pods=`kubectl get pod --namespace=$stackname |   awk '{print $1}'  |  sed -n '1,15p'`
 service=`kubectl get service --namespace=$stackname | awk '{print $1}'`
 #echo $service
 if [ "$pods" != "" ]; then
  for i in $pods
      do 
        if [ "$i" != "NAME" ]; then
           for j in $service
             do
                 if [ "$j" != "NAME" ]; then
		   echo "$i" | grep "$j" >>/dev/null
                   if [ $? -eq 0 ]
                    then 
                    publicIP=`kubectl get service $j --namespace=$stackname  -o json  | grep -E '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)' | grep -v clusterIP `
                    publicIP=`echo $publicIP | sed s/\"//g` >>/dev/null
                     
                    port=`kubectl get service $j --namespace="$stackname" | awk '{print $5}' | grep TCP | awk -F "/" '{print $1}'`
                    publicUrl=$publicIP:$port
                   fi
                fi
             done
          thisIP=`kubectl describe pod $i --namespace=$stackname | grep IP: | awk '{print $2}'`
          image=`kubectl describe pod $i --namespace=$stackname | grep Image\(s\) | awk '{print $2}' | awk -F '/' '{print $3}'`
          printf "%-60s %-15s %-10s %-20s \n" $i $thisIP $publicUrl $image
          publicUrl=""
        fi
     done
 
  #port=`kubectl get service --namespace="$stackname" | awk '{print $5}' | grep TCP | awk -F "/" '{print $1}'`
  #echo -e "\e[1;31m外部访问地址:10.7.0.3:$port \e[0m"
  #getImage  "$stackname"
  #echo "镜像版本:"$images
  #echo "---------------------------------------------------------------------------------"
fi 
}

      check=`heat stack-list | grep $stackname`
      if [ "$check" != "" ]; then 
       getContainerInfo 
      fi

