#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

. $DIR/conf/paas.conf

echo $PAAS_ROOT

export PAAS_VERSION
export PAAS_ROOT
export PAAS_MASTER
export PAAS_BINDIR=$PAAS_ROOT/$PAAS_VERSION/bin
export PAAS_LIBDIR=$PAAS_ROOT/$PAAS_VERSION/lib
export PAAS_SERVERDIR=$PAAS_ROOT/$PAAS_VERSION/etc
export PAAS_CONFDIR=$PAAS_ROOT/conf
export PAAS_LOGDIR="/var/log/paas"
export PAAS_WORKDIR="/var/lib/paas"

export PATH=${PAAS_BINDIR}:${PAAS_SERVERDIR}:$PATH

mkdir ${PAAS_LOGDIR} 2>/dev/null
mkdir ${PAAS_WORKDIR} 2>/dev/null

