#!/bin/bash
# this shell start in docker container (use bridge network)

export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin
export WORKDIR=$( cd ` dirname $0 ` && pwd )

cd $WORKDIR

cadvisor_port=4194

if [ "$CADVISOR_PORT" != "" ]; then
    cadvisor_port=$CADVISOR_PORT
fi

docker0=$(ip route show | awk '/default/ {print $3}')

python ../src/paas-agent.pyc --cadvisor-address=${docker0}:$cadvisor_port
