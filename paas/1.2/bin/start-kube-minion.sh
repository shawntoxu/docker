#!/bin/bash

. $PAAS_ROOT/conf/paas.conf
. $PAAS_LIBDIR/utils.sh

KUBE_PROXY=$PAAS_SERVERDIR/kube-proxy
KUBELET=$PAAS_SERVERDIR/kubelet

killall kubelet > /dev/null 2>&1
killall kube-proxy > /dev/null 2>&1

# start kube-proxy
if [ -z "$KUBE_PROXY_LOG_FILE" ]; then
    KUBE_PROXY_LOG_FILE="$PAAS_LOGDIR/kube-proxy.log"
fi
mkdir -p "$(dirname $KUBE_PROXY_LOG_FILE)"
log "Starting kube-proxy ..."
"$KUBE_PROXY" --master=http://$PAAS_MASTER:8080 --proxy-mode=userspace --logtostderr=true >> $KUBE_PROXY_LOG_FILE 2>&1 &
sleep 2
if ! is_binary_running "$KUBE_PROXY"; then
    log "Failed to start kube-proxy Please check $KUBE_PROXY_LOG_FILE for more detail"
    exit 1
fi

# start kubelet
if [ -z "$KUBELET_LOG_FILE" ]; then
    KUBELET_LOG_FILE=$PAAS_LOGDIR/kubelet.log
fi
mkdir -p "$(dirname $KUBELET_LOG_FILE)"
if [ -z "$KUBELET_LOG_LEVEL" ]; then
    KUBELET_LOG_LEVEL=2
fi
log "Starting kubelet ..."
"$KUBELET" --address=$MY_IP \
    --v=${KUBELET_LOG_LEVEL} \
    --port=$KUBELET_PORT \
    --hostname_override=$MY_IP \
    --api_servers=$PAAS_MASTER:8080 \
    --maximum-dead-containers=10 \
    --minimum-image-ttl-duration=2m0s \
    --logtostderr=true  \
    $KUBELET_OPTS \
    >> ${KUBELET_LOG_FILE} 2>&1 &

