#!/bin/bash

. $PAAS_LIBDIR/utils.sh

export PATH=$PATH:/sbin

if [ $UID != 0 ];
then
    log "Only root can execute this command"
    exit 1
fi

is_docker_chain_existed()
{
    for ((i=0; i<3; i++))
    do
        msg=$(iptables -t filter -L DOCKER 2>&1)
        errno=$?
        if [[ $errno == 0 ]]; then
            return 0
        else
            echo $msg | grep "No chain" && return 1
        fi
        log_info "errno=$errno; msg=$msg"
        sleep 1
    done

    return 2
}

is_docker_chain_existed
if [[ $? == 1 ]]; then
    log_error "DOCKER chain does not exist in iptables. Create it."
    iptables -t filter -N DOCKER
fi
