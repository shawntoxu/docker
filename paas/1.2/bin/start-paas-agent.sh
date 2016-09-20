#!/bin/bash

. $PAAS_LIBDIR/utils.sh

log "Start paas-agent ..."
ok=0
kubectl get ds paas-agent > /dev/null 2>&1 || ok=1
if [[ $ok == 1 ]]; then 
    kubectl create -f $PAAS_ROOT/$PAAS_VERSION/conf/paas-agent.yml
fi

log "paas-agent started."
