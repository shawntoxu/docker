#!/bin/bash
#kubectl create -f ./heat_vn_ali.json
stackname=config-center
heatconf=heat_java1_ali.json
check=`heat stack-list | grep $stackname`
 if [ "$check" != "" ]; then 
     heat stack-update  $stackname -f  $heatconf >> /tmp/heat-client.log
     echo "----------------update  resource---------"
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
echo "------------run container---------------"
heat stack-create -f $heatconf  $stackname >> /tmp/heat-client.log
 
for i in $(seq 1 13)
    do
     complete=`heat stack-list | grep $stackname | awk -F "|" '{print $4}'` 
     
     if [ "$complete" != "CREATE_COMPLETE" ]; then
         printf ". "  
         sleep 1 
     fi 
    done
fi
 
