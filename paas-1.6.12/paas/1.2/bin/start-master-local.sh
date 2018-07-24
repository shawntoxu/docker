#!/bin/bash

. $PAAS_ROOT/conf/paas.conf
. $PAAS_LIBDIR/utils.sh

KUBE_APISERVER=$PAAS_SERVERDIR/kube-apiserver
KUBE_CM=$PAAS_SERVERDIR/kube-controller-manager
KUBE_SCHEDULER=$PAAS_SERVERDIR/kube-scheduler

if [ -z "$KUBE_API_LOG_FILE" ]; then
    KUBE_API_LOG_FILE="$PAAS_LOGDIR/kube-apiserver.log"
fi

if [ -z "$KUBE_SCH_LOG_FILE" ]; then
    KUBE_SCH_LOG_FILE="$PAAS_LOGDIR/kube-scheduler.log"
fi

if [ -z "$KUBE_CM_LOG_FILE" ]; then
    KUBE_CM_LOG_FILE="$PAAS_LOGDIR/kube-controller-manager.log"
fi

# check if current host is the master
if [ $PAAS_MASTER != "$MY_IP" ]; then
    log "The host <$MY_IP> is not the kubernetes master"
    exit 1
fi

# stop kube-master processes
log "Stoping master processes ..."
killall kube-apiserver > /dev/null 2>&1
killall kube-controller-manager  > /dev/null 2>&1
killall kube-scheduler > /dev/null 2>&1

etcd_servers=""
for host in $ETCD_HOSTS
do
    if [ "$etcd_servers" == "" ]; then
        etcd_servers=http://$host:4001
    else
        etcd_servers=$etcd_servers,http://$host:4001
    fi  
done

log "Starting master <$MY_IP> ..."

ulimit -n 65536

log "start kube-apiserver..."
mkdir -p "$(dirname $KUBE_API_LOG_FILE)"
if [ -z "$KUBE_API_LOG_LEVEL" ]; then
    KUBE_API_LOG_LEVEL=2
fi
"$KUBE_APISERVER" --insecure-bind-address=$MY_IP \
    --bind-address=$MY_IP \
    --port=8080 \
    --kubelet_port=$KUBELET_PORT  \
    --etcd_servers=${etcd_servers} \
    --logtostderr=true \
    --service-cluster-ip-range=${KUBE_API_SERVICE_CLUSTER_IP_RANGE} \
    ${KUBE_API_SECURITY_OPTS} \
    --v=${KUBE_API_LOG_LEVEL} \
    >> $KUBE_API_LOG_FILE 2>&1 &
sleep 2
if ! is_binary_running "$KUBE_APISERVER"; then
    log "Failed to start kube-apiserver. Please see $KUBE_API_LOG_FILE for more detail"
    exit 1
fi

log "start kube-controller-manager..."
mkdir -p "$(dirname $KUBE_CM_LOG_FILE)"
if [ -z "$KUBE_CM_LOG_LEVEL" ]; then
    KUBE_CM_LOG_LEVEL=2
fi
"$KUBE_CM" --master=$MY_IP:8080 \
    --logtostderr=true \
    --v=${KUBE_CM_LOG_LEVEL} \
    >> $KUBE_CM_LOG_FILE 2>&1 &
sleep 2
if ! is_binary_running "$KUBE_CM"; then
    log "Failed to start kube-controller-manager. Please see $KUBE_CM_LOG_FILE for more detail"
    exit 1
fi

log "start kube-scheduler..."
scheduler_policy_file=
#if [ -f "$PAAS_ROOT/conf/scheduler-policy-config.json" ];
#then
#    scheduler_policy_file="$PAAS_ROOT/conf/scheduler-policy-config.json"
#fi
mkdir -p "$(dirname $KUBE_SCH_LOG_FILE)"
"$KUBE_SCHEDULER" --logtostderr=true \
    --master=$MY_IP:8080 \
    --policy-config-file=$scheduler_policy_file \
    >> ${KUBE_SCH_LOG_FILE} 2>&1 &
sleep 2
if ! is_binary_running "$KUBE_SCHEDULER"; then
    log "Failed to start kube-scheduler. Please see $KUBE_SCH_LOG_FILE for more detail"
    exit 1
fi
