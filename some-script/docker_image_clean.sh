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

white_list=(
    "gcr.io/google_containers/pause"
    "registry"
    "myregistry:5000/web_base"
    "myregistry:5000/java_base"
    "myregistry:5000/node_base"
)

check_white_list()
{
    in=$1
    for str in ${white_list[@]}
    do
        #echo "in:" $in " str: " $str
        if [[ $str = $in ]]; then
            return 0 
        fi
    done
    return -1 
}

clean_images()
{
    log "begin clean images..."
    containter_list_file='/tmp/paas/docker_containter_list'

    mkdir /tmp/paas 2>/dev/null
    docker ps > ${containter_list_file}

    docker images | while read line
    do
        #echo $line
        fields=($line)
        repository=${fields[0]}
        tag=${fields[1]}
        image_id=${fields[2]}
        duration_type=${fields[4]}

        #if [[ "$repository" = "gcr.io/google_containers/pause" ]]; then
        #    continue
        #fi
        #if [ "$repository" = "registry" ]; then
        #    continue
        #fi
        check_white_list "$repository" 
        if [[ $? = 0 ]]; then
            continue
        fi

        grep $repository:$tag ${containter_list_file} >/dev/null
        if [ $? != 0 ]; then
            # No containter of the image is running, so delete the image.
            #msg=`docker rmi $repository:$tag 2>&1`
            #echo "docker rmi $repository:$tag"
            msg=`docker rmi -f $image_id 2>&1`
            if [ $? == 0 ]; then
                log "[INFO] $repository:$tag $image_id is deleted"
            fi
        fi
    done

    rm ${containter_list_file}
    log "clean image completely."
}

log_prepare
clean_images $1
