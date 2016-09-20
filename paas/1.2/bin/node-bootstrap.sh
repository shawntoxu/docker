#!/bin/bash

is_master_ok()
{
    if !(curl -s $PAAS_MASTER:4001/v2/keys 2>&1>/dev/null); then
        return 1
    fi
    if !(curl -s $PAAS_MASTER:8080/api/v1/nodes 2>&1>/dev/null); then
        return 1
    fi
    return 0
}

while true
do
    if (is_master_ok); then
        break
    fi
    echo "master is not OK"
    sleep 5
done

start-minion-local.sh

