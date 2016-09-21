#!/usr/bin/env python
#coding=utf-8
from datetime import datetime
import getopt
import json
import math
import os
import sys
import time
import datetime
import requests
import random
import string
'''
@author: shawn.wang
query k8s pod　log (stdout)
'''
SERVER='10.7.0.1'
SERVER_URL='http://%s:8080'
RUN_ONCE_NAMESPACE='RC_NAME'
watch_url='/api/v1/watch/namespaces/default/pods/%s'
pod_url='/api/v1/namespaces/%s/pods/%s'
create_pod_url='/api/v1/namespaces/%s/pods/'
pod_log_url='/api/v1/namespaces/%s/pods/%s/log'
#status_url='/api/v1/watch/namespaces/default/pods/%s'
TMPL_PATH='/home/paas/work/testJob/pod-tmplate.json'
rc_url='/api/v1/namespaces/%s/replicationcontrollers/%s'
rc_url2='/api/v1/namespaces/%s/replicationcontrollers'


def query_pod_log(pod_name):
    url = (SERVER_URL + pod_log_url) % (SERVER, RUN_ONCE_NAMESPACE, pod_name)
    #print "log url:%s" % url
    r = requests.get(url)
    if r.status_code == 200:
        return r.content
    else:
        return None
    #para = request.args
    #r = requests.get(url,params=para)
    #return resent_req(url, 'GET', None)

if __name__ == '__main__':
    #
    log = query_pod_log('mytest-pod')
    print log 
