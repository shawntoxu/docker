#!/bin/bash

. $PAAS_LIBDIR/utils.sh

if ! $PAAS_BINDIR/start-flanneld-local.sh; then
    exit 1
fi

if ! $PAAS_BINDIR/start-docker.sh; then
    exit 1
fi

if ! $PAAS_BINDIR/start-kube-minion.sh; then
    exit 1
fi
#$PAAS_BINDIR/start-paas-agent.sh
