#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

log_file="/var/log/paas/docker_image_clean.log"

log_prepare()
{
    mkdir -p /var/log/paas/ > /dev/null 2>&1
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
    #echo "[`date '+%Y-%m-%d %H:%M:%S'`] "$msg"" >> $log_file
    echo "[`date '+%Y-%m-%d %H:%M:%S'`] "$msg""
}

clean_images()
{
    log "begin clean images..."
    containter_list_file='/tmp/paas/docker_containter_list'

    mkdir /tmp/paas 2>/dev/null
    docker ps > ${containter_list_file}

    docker images | while read line
    do
        fields=($line)
        repository=${fields[0]}
        tag=${fields[1]}
        image_id=${fields[2]}
        duration_type=${fields[4]}

        if [[ "$repository" = "gcr.io/google_containers/pause" ]]; then
            continue
        fi
        if [ "$repository" = "registry" ]; then
            continue
        fi

        grep $repository:$tag ${containter_list_file} >/dev/null
        if [ $? != 0 ]; then
            # No containter of the image is running, so delete the image.
            msg=`docker rmi $repository:$tag 2>&1`
            if [ $? == 0 ]; then
                log "[INFO] $repository:$tag is deleted"
            fi
        fi
    done

    rm ${containter_list_file}
    log "clean image completely."
}

log_prepare
clean_images $1

#import crontab, never done in this file, just for studying
#bak_file="/tmp/crontab.bak"
#crontab -l > $bak_file
#echo "#check docker registry every minute. created by allen.gao@ndpmedia.com" >> $bak_file
#echo "23 1 * * * /root/paas/script/docker_container_clean.sh > /dev/null 2>&1" >> $bak_file
#crontab $bak_file
