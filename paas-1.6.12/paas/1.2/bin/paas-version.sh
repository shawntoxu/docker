#!/bin/bash

echo paas: $PAAS_VERSION
echo ========================================================
echo kubernetes: $(kube-apiserver --version | awk '{print$2}')
echo etcd:       $(etcd --version | awk '{print$3}')
echo docker:     $(docker --version | awk '{print$3,$4,$5}')
echo flanneld:   $(flanneld --version 2>&1)
