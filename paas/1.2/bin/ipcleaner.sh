#! /bin/bash

set -eo pipefail

#usage: sudo ./ipcleaner.sh [--all]

allips=()
all=false
dstdir=/dianyi/log/

log_file="/var/log/paas/ipcleaner.log"

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
    echo "[`date '+%Y-%m-%d %H:%M:%S'`] "[INFO] $msg"" >> $log_file
}

function delete_older() {
    targetdir=$1
    if [[ ! -d ${targetdir} ]]; then
        log "Directory ${targetdir} does not exist, skipping."
        return
    fi
    log "Delete older unused ip directories from $targetdir"

    for dir in $(find $targetdir -maxdepth 1 -mindepth 1 -mtime +1)
    do
        dir=$(basename $dir)
        if [[ "${dir}" =~ [^0-9.] ]]; then
            log "Not a ip: ${dir}"
        else
            if [[ ${allips[@]} =~ "${dir}" ]]; then
                log "In use ${dir}"
            else
                log "Deleting ${dir}"
                rm -rf ${targetdir}/${dir}
            fi
        fi
    done
}


function delete_unused_all() {
  targetdir=$1
  if [[ ! -d ${targetdir} ]]; then
        log "Directory ${targetdir} does not exist, skipping."
        return
  fi
  log "Delete unused ip directories from $targetdir"
  for dir in $(ls -d ${targetdir}/* 2>/dev/null)
  do
        dir=$(basename $dir)
        if [[ "${dir}" =~ [^0-9.] ]]; then
                log "Not a ip: ${dir}"
        else
                if [[ ${allips[@]} =~ "${dir}" ]]; then
                        log "In use ${dir}"
                else
                    log "Deleting ${dir}"
                    rm -rf ${targetdir}/${dir}
                fi
 
        fi
  done
}

if [ $UID != 0 ]; then
    log "You need to be root to use this script."
    exit 1
fi

docker_bin=$(which docker.io || which docker)
if [ -z "$docker_bin" ] ; then
    log "Please install docker. You can install docker by running \"wget -qO- https://get.docker.io/ | sh\"."
    exit 1
fi

if [ "$1" = "--all" ]; then
        all=true
else if [ -n "$1" ]; then
        echo "Cleanup host logs : remove logs 24 hours ago by default in /dianyi/log/ "
        echo "Usage: ${0##*/} [--all]"
        echo "   --all: remove all hosts logs containers exit"
        exit 1
fi
fi

# Make sure that we can talk to docker daemon. If we cannot, we fail here.
docker info >/dev/null

#All ip from all containers
i=0
for container in `${docker_bin} ps -q `; do
        #add all ip from this container to the list of volumes
        for vip in `${docker_bin} inspect --format '{{.NetworkSettings.IPAddress}}' ${container}`; do
                if [[ ${vip} =~ [0-9.] ]]; then
                        allips[i]=${vip}
                        #echo ${vip}
                        i=`expr $i + 1`
               fi
        done
done


for sdir in $(find $dstdir -maxdepth 1 -mindepth 1)
do
    log "======== Deleting $sdir ========="
    if [ "${all}" = false ]; then
        delete_older ${sdir}
    else
        delete_unused_all ${sdir}
    fi
done
