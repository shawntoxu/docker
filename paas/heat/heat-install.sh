#!/bin/bash
export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin
export WORKDIR=$( cd ` dirname $0 ` && pwd )
cd "$WORKDIR" || exit 1
registry=myregisty:5000
get_my_ip()
{
    my_ip=$(ip route get 1.0.0.0 | head -1 | cut -d' ' -f8)
    if [ ! -n "$my_ip" ]; then  
      my_ip=$(ifconfig eth0 | grep -oP 'inet addr:\K\S+')
      if [ ! -n "$my_ip" ]; then
            my_ip=$(hostname -I|cut -d' ' -f1)
      fi
    fi

    echo $my_ip
}

pre_check()
{
    if [[ -z "$my_ip" ]]; then
        echo "FATAL: ElasticIP does not exist! exit."
        exit 1
    fi

    # You MUST write k8s certification into this file
    if [ ! -f "$KUBE_CERT" ]; then
        echo "$KUBE_CERT is not ready. exit."
        exit 1
    else
        echo "Got $KUBE_CERT, will install heat."
    fi

    if [[ "$KUBE_CERT" != "${PERSIST_DISK}/docker/heat/.kube_cert" ]]; then
        mkdir -p ${PERSIST_DISK}/docker/heat/
        cp $KUBE_CERT ${PERSIST_DISK}/docker/heat/.kube_cert
    fi

   
    local containers=$(docker ps -a | grep "$registry" |cut -d' ' -f1)
    if [[ ! -z "$containers" ]]; then
        echo "remove all exist heat containers of $registry"
        docker rm -f $containers
    fi
    echo "NOTE: Will reuse mysql data in ${PERSIST_DISK}/docker/mysql."
}

wait_for_service_ready()
{
  local PORT=$1
  attempt=0
  while true; do
    echo Attempt "$(($attempt+1))" to check for $PORT
    local ok=1
    curl --connect-timeout 3 http://${my_ip}:$PORT || ok=0
    echo
    if [[ ${ok} == 0 ]]; then
      if (( attempt > 10 )); then
        echo
        echo -n "failed to start $PORT on ${my_ip}. You need to run " >&2
        echo -n "[sudo /srv/salt/kube-bins/heat_restart.sh] ">&2
        echo "manually on Master host." >&2
        exit 1
      fi
    else
      echo " [$PORT running]"
      break
    fi
    echo " [$PORT not working yet]"
    attempt=$(($attempt+1))
    sleep 5
  done
}

install_mysql()
{
    echo 'pulling $registry/mysql:5.5...'
    docker pull $registry/heat-mysql:5.5 > /dev/null

    mkdir -p ${PERSIST_DISK}/docker/mysql
    docker run --name mysql -h mysql \
        -v ${PERSIST_DISK}/docker/mysql:/var/lib/mysql \
        -e MYSQL_ROOT_PASSWORD=Letmein123 \
        -p 23306:3306 \
        -d $registry/heat-mysql:5.5
    echo 'sleep 10s to ensure mysql is ready'
    sleep 10 
    echo 'intalled mysql'
}

install_rabbitmq()
{
    echo 'pulling $registry/rabbitmq'
    docker pull $registry/heat-rabbitmq > /dev/null

    docker run -d \
        --hostname rabbitmq \
        --name rabbitmq \
        -e RABBITMQ_DEFAULT_PASS=Letmein123 \
        $registry/heat-rabbitmq
    echo 'sleep 2s to ensure rabbitmq is ready..'
    sleep 2 
    echo 'installed rabbitmq'
}

install_keystone()
{
    echo 'pulling $registry/keystone:juno...'
    docker pull $registry/keystone:juno > /dev/null

    docker run -d \
        --link mysql:mysql\
        -e OS_TENANT_NAME=admin \
        -e OS_USERNAME=admin \
        -e OS_PASSWORD=ADMIN_PASS \
        -p 35357:35357\
        -p 5000:5000 \
        --name keystone -h keystone $registry/keystone:juno
    wait_for_service_ready 35357
}

install_heat()
{
    echo 'pulling $registry/heat:kilo-k8s-1.2...'
    docker pull $registry/heat:kilo-k8s-1.2 > /dev/null

    docker run \
      -p 8004:8004 \
      --link mysql:mysql\
      --link rabbitmq:rabbitmq\
      --link keystone:keystone\
      -v /var/log/heat:/var/log/heat \
      -v ${PERSIST_DISK}/docker/heat:/root \
      --hostname heat \
      --name heat \
      -e KEYSTONE_HOST_IP=keystone \
      -e HOST_IP=heat \
      -e MYSQL_HOST_IP=mysql \
      -e MYSQL_USER=root \
      -e MYSQL_PASSWORD=Letmein123 \
      -e ADMIN_PASS=ADMIN_PASS \
      -e RABBIT_HOST_IP=rabbitmq \
      -e RABBIT_PASS=Letmein123 \
      -e HEAT_PASS=Letmein123 \
      -e HEAT_DBPASS=Letmein123 \
      -e HEAT_DOMAIN_PASS=Letmein123 \
      -e ETC_HOSTS="${hosts_conf}" \
      -d $registry/heat:kilo-k8s-1.2
    wait_for_service_ready 8004
}

install_heatclient()
{

    echo 'install heat over. Will install heat client...'
    echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu trusty-updates/kilo main" > /etc/apt/sources.list.d/cloudarchive-kilo.list
    apt-get update > /dev/null 2>&1
    apt-get install -y --force-yes python-heatclient > /dev/null

    HEAT_RC=/root/heatrc
    touch ${HEAT_RC}
    sed -i '/^export OS_/d' ${HEAT_RC}
    echo "export OS_PASSWORD=ADMIN_PASS" >> ${HEAT_RC}
    echo "export OS_AUTH_URL=http://${my_ip}:35357/v2.0" >> ${HEAT_RC}
    echo "export OS_USERNAME=admin" >> ${HEAT_RC}
    echo "export OS_TENANT_NAME=admin" >> ${HEAT_RC}
    source ${HEAT_RC}

    sed -i '/heatrc/d' /root/.bashrc
    echo ". ${HEAT_RC}" >> /root/.bashrc
    env | grep "^OS_"

    heat resource-type-list | grep Google
    heat stack-list
    echo "heat check over."
}

check_heat_client(){

  check=`dpkg --list | grep heatclient`
  if [ "$check" != "" ];
  then
    echo "heat client has install ."
  else
   install_heatclient
  fi

}

hosts_conf=$1
KUBE_CERT=$2

my_ip=$(get_my_ip)
#my_ip=$(ec2metadata | grep public-ipv4 |cut -d" " -f2)

PERSIST_DISK=/pdata

if [[ $# != 2 ]]; then
    echo "usage: $0 hosts_conf kube_cert_file"
    echo "e.g  : $0 bash heat_restart.aws_shawntest.sh  \"172.30.80.23 test.k8s.cc\" /opt/paas/auth/ssl-cert/server.crt"
    exit 1
fi


pre_check
install_mysql
install_rabbitmq
u need to run 
install_keystone
install_heat
check_heat_client
#install_heatclient
