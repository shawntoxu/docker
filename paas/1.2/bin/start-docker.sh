#!/bin/bash

. $PAAS_ROOT/conf/paas.conf
. $PAAS_LIBDIR/utils.sh

DOCKER_VERSION="1.8.3"
DOCKER_LOG_FILE="$PAAS_LOGDIR/docker.log"

install_docker()
{
    # wget -qO- https://get.docker.com/ | sh

    if [[ $(which docker) ]]; then
        if [[ $(docker --version | grep $DOCKER_VERSION) ]]; then
            log "docker $DOCKER_VERSION already installed"
        else
            log "The installed docker is $(docker version | grep "Client version" | cut -d ' ' -f 3)"
            log "Please uninstall the docker and run this script again"
            log "Stopped"
            exit 1
        fi
    else
        echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main" > /etc/apt/sources.list.d/docker.list
        apt-get update
        apt-get install docker-engine=1.8.3-0~trusty
    fi

    #log $(docker version)
    #log "install docker OK."
}

aufs_check()
{
        if ! grep -q aufs /proc/filesystems && ! sh -c 'modprobe aufs'; then
                if uname -r | grep -q -- '-generic' && dpkg -l 'linux-image-*-generic' | grep -q '^ii' 2>/dev/null; then
                        kern_extras="linux-image-extra-$(uname -r) linux-image-extra-virtual"
                        apt-get update
                        apt-get install -y -q "$kern_extras" || true

                        if ! grep -q aufs /proc/filesystems && ! sh -c 'modprobe aufs'; then
                                log "we still have no AUFS. Docker may not work. Exit."
                                exit 1
                        fi
                else
                        log "Warning: current kernel is not supported by the linux-image-extra-virtual package.  We have no AUFS support.  Consider installing the packages linux-image-virtual kernel and linux-image-extra-virtual for AUFS support. Exit."
                        exit 1
                fi
        fi
}

aufs_check
install_docker

killall docker > /dev/null 2>&1
service docker stop > /dev/null 2>&1
iptables -t nat -F

# start docker
log "Starting docker ..."
mkdir -p "$(dirname $DOCKER_LOG_FILE)"
insecure_registries=""
for registry in ${DOCKER_INSECURE_REGISTRY_LIST}
do
    insecure_registries="$insecure_registries --insecure-registry $registry"
done

source /run/flannel/subnet.env
ip link del docker0 1>/dev/null 2>&1
if [ -z "$DOCKER_LOG_LEVEL" ]; then
    DOCKER_LOG_LEVEL=warning
fi

#set host limit 
ulimit -n 65535

# version > 1.8.3   daemon 
# add ulimit set 
#docker daemon  --default-ulimit nofile=65535:65535 --default-ulimit nproc=65535:65535 --bip=${FLANNEL_SUBNET} --mtu=${FLANNEL_MTU} ${insecure_registries} --log-level=${DOCKER_LOG_LEVEL} --storage-driver=${STORAGE} >> $DOCKER_LOG_FILE 2>&1 &

docker -d --bip=${FLANNEL_SUBNET} --mtu=${FLANNEL_MTU} ${insecure_registries} --log-level=${DOCKER_LOG_LEVEL} --storage-driver=aufs >> $DOCKER_LOG_FILE 2>&1 &
sleep 2
if ! is_binary_running "docker"; then
    log "Failed to start docker. Please check $DOCKER_LOG_FILE for more detail"
    exit 1
fi


