#! /bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

log_file="/root/paas/script/docker_registry_chk.log"

log_prepare()
{
    touch "$log_file"
    local SIZE=`ls -s $log_file | awk '{print$1}'`
    if [ $SIZE -ge 10240 ];
    then
        echo "[`date '+%Y-%m-%d %H:%M:%S'`] begin" > $log_file
    fi
}

log()
{
    local msg=$*        
    echo "[`date '+%Y-%m-%d %H:%M:%S'`] "$msg"" >> $log_file
}

# check if the docker registry container is running, start a new one if it not exist
check()
{
    cid=$(sudo docker ps | grep "registry:2" | awk '{print $1}')
    if [[ "$cid" != "" ]];
    then        
        log "[INFO] Docker registry exists, check OK."
        return 0
    else
        log "[ERROR] Docker registry exited, need start a new registry container."
        return 1
    fi
}

log_prepare
check
if [[ $? != 0 ]]; then
    sudo docker run -d -e "REGISTRY_STORAGE_DELETE_ENABLED=True" -p 5000:5000 --name=registry --restart=always -v /mnt/paas_cd/paas/registry_data:/var/lib/registry registry:2
    sleep 1
    check
    if [[ $? != 0 ]]; then
        log "[ERROR] Docker registry container start failed."
    else
        log "[INFO] Docker registry recovered now."
    fi
fi

# add to crontab check server 
#* */1 * * * /script/docker_registry_check.sh > /dev/null 2>&1
