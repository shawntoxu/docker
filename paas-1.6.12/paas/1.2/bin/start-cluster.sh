#!/bin/bash

. ../cluster.conf

start_etcd()
{
    for host in $ETCD_HOSTS
    do
        echo "starting etcd on host <$host> ..."
        ssh -f $host "cd $CLUSTER_ROOT/paas-cluster/kubernetes_cluster/script/; ./start-etcd.sh"
    done
}

./update_files.sh

#start_etcd
