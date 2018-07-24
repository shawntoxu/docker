#!/bin/bash

. $PAAS_CONFDIR/paas.conf
. $PAAS_LIBDIR/utils.sh

ETCD="$PAAS_SERVERDIR/etcd"

get_cluster_opt()
{
    hosts=($1)
    node_names=($2)
    i=0

    for ip in $1
    do
        #log "node_names[$i]=${node_names[$i]}"
        if [ -z $init_cluster_opt ]; then
            init_cluster_opt="${node_names[$i]}=http://$ip:2380"
        else
            init_cluster_opt="$init_cluster_opt,${node_names[$i]}=http://$ip:2380"
        fi

        ((i++))
    done
}

node_name=

#
# $1 is etcd cluster nodes
# such as : "192.168.1.120 192.168.1.121 192.168.1.122"
#
can_run_etcd()
{
    i=0
    node_names=($ETCD_NODE_NAMES)

    for ip in $1
    do
        if [ "$ip" == "$MY_IP" ]; then
            node_name=${node_names[$i]}
            #log "node_name=$node_name"
            return
        fi
        ((i++))
    done

    return 1
}

if can_run_etcd "$ETCD_HOSTS"; then
    log "Starting etcd ..."
else
    log "This host is not a etcd host. ETCD_HOSTS=${ETCD_HOSTS}"
    exit 1
fi

init_cluster_opt=
get_cluster_opt "$ETCD_HOSTS" "$ETCD_NODE_NAMES"

killall etcd 2>/dev/null

if [ -z "$ETCD_LOG_FILE" ]; then
    ETCD_LOG_FILE="$PAAS_LOGDIR/etcd.log"
fi

mkdir -p "$(dirname $ETCD_LOG_FILE)"

"$ETCD" -name=$node_name \
    -initial-advertise-peer-urls=http://$MY_IP:2380 \
    -advertise-client-urls=http://$MY_IP:4001 \
    -listen-peer-urls=http://0.0.0.0:2380 \
    -listen-client-urls="http://0.0.0.0:4001" \
    -initial-cluster "$init_cluster_opt" \
    -data-dir=$ETCD_DATA_PATH \
    -initial-cluster-token "etcd-cluster-23" \
    -initial-cluster-state new \
    >> $ETCD_LOG_FILE 2>&1 &


sleep 5
if is_binary_running $ETCD; then
    log "Starting etcd done."
else
    log "Failed to start etcd. Please check $ETCD_LOG_FILE for more detail."
fi

