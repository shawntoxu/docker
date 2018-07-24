#!/bin/bash

. $PAAS_LIBDIR/utils.sh

binaries="kube-apiserver kubelet kube-controller-manager kube-scheduler kube-proxy docker flanneld etcd"

for binary in $binaries
do
    if is_binary_running "$binary"; then
        log "Stoping $binary"
        killall "$binary" 2>/dev/null
    fi
done

log "done"
