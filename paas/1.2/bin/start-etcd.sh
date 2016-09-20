#!/bin/bash

. $PAAS_ROOT/paas.conf
. $PAAS_LIBDIR/utils.sh

log "start etcd on hosts <$ETCD_HOSTS>"

mkdir /tmp/paas/

rm /tmp/paas/etcd_hosts
echo "[etcd_hosts]" > /tmp/paas/etcd_hosts

for etcd_host in ${ETCD_HOSTS}
do
    log "etcd_host = $etcd_host"
    echo $etcd_host >> /tmp/paas/etcd_hosts
done

ansible-playbook -i /tmp/paas/etcd_hosts $PAAS_ROOT/$PAAS_VERSION/conf/start.yml

