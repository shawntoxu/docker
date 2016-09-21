#coding=utf8
import sys
import urllib2
import json
from copy import deepcopy
import time
import datetime
import os
import subprocess

'''
#!/usr/bin/env python
@author: shawn.wang
get image name from k8s 
'''

SERVER_ADDRESS = "172.30.10.10:8080"
RC_NAME        = "py-test"
NAMESPACE      = "default"

def get_images(server,namespace,rc_name):
    try:
        
        url = 'http://{}/api/v1/namespaces/{}/replicationcontrollers/{}'.format(server,namespace, rc_name)
        print url 
        #if server != None:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        recv_json = json.load(response)
        #d1 = json.dumps(b,sort_keys=True,indent=2)
        # one rc one containers 
        image = recv_json.get("spec").get("template").get("spec").get("containers")[0]["image"] #.items()#.get("image")
        print image
    except Exception,e:
        print "error"
def main(argv):
    SERVER_ADDRESS=argv[0].strip()
    NAMESPACE=argv[1].strip()
    RC_NAME=argv[2].strip()
    get_images(SERVER_ADDRESS,NAMESPACE,RC_NAME)

if __name__ == '__main__':
     #get_images(SERVER_ADDRESS,RC_NAME)
     main(sys.argv[1:])
