#! /bin/bash
. $PAAS_LIBDIR/utils.sh

export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin


if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

clean_exited_containers()
{
    cnt1=$(sudo docker ps -a|grep -E Exit\|Dead\|Created|wc -l)
    if [[ $cnt1 > 0 ]]; then
        cnt2=$(sudo docker ps -a|grep -E Exit\|Dead\|Created|cut -d' ' -f1|xargs docker rm -v | wc -l)
        log_info "successfull removed exited containers: $cnt2"
    else
        log_info "there is no exited container, exit."
    fi
}

clean_exited_containers
