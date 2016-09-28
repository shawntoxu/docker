#!/bin/bash

usage(){
        echo "$0 stackname  push2address registry-path image-name image-version heat_json"
        echo "e.g. $0  my-app  dev app  gkt-content-web 1.0 heat_config-center_aws.json "
}


if [ $# != 6 ]; then
      usage && exit
fi

# set k8s master 
export KUBERNETES_MASTER=172.30.10.122:8080
# set heat env
export OS_AUTH_URL=http://172.30.10.155:35357/v2.0
export OS_PASSWORD=ADMIN_*
export OS_USERNAME=admin
export OS_TENANT_NAME=admin


workdir=$( cd ` dirname $0 ` && pwd )
#set APP ENV
dbconfig=dev

stackname=$1
push2address=$2
registry_path=$3
image_name=$4
image_version=$5
heat_json=$6
image_url=$registry_path/$image_name:$image_version
# build images && push to registry
#echo "----build images && push---------------------"
#sudo sh $workdir/image_build/build.sh $push2address $image_url
#if [ $? -ne 0 ]; then
#    exit  
#fi

#generator heat json 
jsonname="$stackname"_"$image_name":"$image_version"
heatconf=$workdir/history/$jsonname.json
sudo cp $workdir/template/$heat_json $heatconf 

sudo sed -i s/default/$stackname/g $heatconf

#change env & 
#sudo sed -i s/gkt-content-web/$image_name/g $heatconf 
#sudo sed -i s/31000/40001/g $heatconf
#sudo sed -i s/v1.0/$image_version/g $heatconf
sudo sed -i s/@/$image_version/g $heatconf


#sudo sed -i s/product/$dbconfig/g $heatconf

function createResource(){
check=`heat stack-list | grep $stackname`
 if [ "$check" != "" ]; then 
     heat stack-update  $stackname -f  $heatconf >> /tmp/heat-client.log
     echo "----------------update  resource $stackname---------"
     for i in $(seq 1 15)
        do 
            res=`heat stack-list | grep $stackname | awk -F "|" '{print $4}'` 
            if [ "$res" != "CREATE_COMPLETE" ]; then
                printf ". "
                sleep 1 
            fi
        done
 fi   

if [ "$check" == "" ]; then
echo "------------run  container---------------"
heat stack-create -f $heatconf  $stackname >> /tmp/heat-client.log
 
for i in $(seq 1 15)
    do
     complete=`heat stack-list | grep $stackname | awk -F "|" '{print $4}'` 
     
     if [ "$complete" != "CREATE_COMPLETE" ]; then
         printf ". "  
         sleep 1 
     fi 
    done
fi

#get pod innerIP
pods=` kubectl get pod --namespace=$stackname  |  awk '{print $1}' | sort |  sed -n '1p'`
for i in $pods
  do 
     echo ""
     echo "内部ip:"` kubectl describe pod $i --namespace=$stackname | grep IP: | awk '{print $2}'`
  done

#bash  $workdir/web-images/clean_log.sh

echo "外部访问地址:$dport"  
}

#createResource
