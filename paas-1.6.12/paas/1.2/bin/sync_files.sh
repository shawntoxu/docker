#!/bin/bash

. $PAAS_CONFDIR/paas.conf

if [ $# -ge 1 ]; then
    node_list=$@
else
    node_list=$(kubectl get node | tail -n +2 | awk {'print$1'})
fi

for node in $node_list
do
    echo "start sync files for $node"
    $COPY_CMD -r $PAAS_ROOT/* $node:$PAAS_ROOT/
    echo "end sync files for $node"
done

