#!/bin/bash

. $PAAS_CONFDIR/paas.conf
. $PAAS_LIBDIR/utils.sh

FLANNELD=$PAAS_SERVERDIR/flanneld
FLANNELD_LOG_FILE="$PAAS_LOGDIR/flanneld.log"

killall flanneld > /dev/null 2>&1
mkdir -p /var/log/flannel/  2>/dev/null

etcd_servers=""
for host in $ETCD_HOSTS
do
    if [ "$etcd_servers" == "" ]; then
        etcd_servers=http://$host:4001
    else
        etcd_servers=$etcd_servers,http://$host:4001
    fi  
done

mkdir -p "$(dirname $FLANNELD_LOG_FILE)"

# start flannel
log "Starting flanneld ..."
etcd_hosts=($ETCD_HOSTS)
if [[ $(curl -L http://${etcd_hosts[0]}:4001/v2/keys/coreos.com/network/config 2>/dev/null | grep "Key not found") ]]; then
    echo "curl -L http://${etcd_hosts[0]}:4001/v2/keys/coreos.com/network/config -XPUT --data-urlencode value@${PAAS_CONFDIR}/flannel-config.json > /dev/null 2>&1"
    curl -L http://${etcd_hosts[0]}:4001/v2/keys/coreos.com/network/config -XPUT --data-urlencode value@${PAAS_CONFDIR}/flannel-config.json > /dev/null 2>&1
fi

"$FLANNELD" --etcd-endpoints=${etcd_servers} >> ${FLANNELD_LOG_FILE} 2>&1 &
sleep 5

if is_binary_running "$FLANNELD"; then
    exit 0
else
    log "Failed to start flanneld. Please check ${FLANNELD_LOG_FILE} for more detail."
    exit 1
fi

