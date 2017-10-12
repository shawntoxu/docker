# -*- coding: UTF-8 -*-
import  thread
import time
import threading
import config
from cache import *

'''
cache app info 
by shawn
'''

# define the app list
K8S_IP=config.K8S_IP

def get_applist():
    APP=[]
    r = requests.get('http://{}:8080/api/v1/namespaces'.format(K8S_IP))
    if r.status_code == 200 or r.status_code == 201 \
            or r.status_code == 204 or r.status_code == 202:

            res = r.json()
            for ns in res['items']:
                #print ns['metadata']['name']
                if ns['metadata']['name'] != 'default':
                    APP.append(ns['metadata']['name'])
    return APP

def get_application(application_name):
    session = requests.session()
    url = 'http://{}:8080/api/v1/namespaces/{}/pods'.format(K8S_IP,application_name)
    reply = session.get(url)
    pod_list_json = reply.json()['items']

    url = 'http://{}:8080/api/v1/namespaces/{}/replicationcontrollers'.format(K8S_IP, application_name)
    reply = session.get(url)
    rc_list_json = reply.json()['items']
    LOG.info("thread " + application_name + " running .")

    try:
        stack = heat_client.get_stack(application_name)
        stack_json = stack.to_dict()
        res=heat_client.get_resource_list(application_name)
        res=write_cache(application_name,res)

    except Exception, e:
        LOG.warning(type(e))
        LOG.warning(e)
        return None



class CacheThread(threading.Thread):

    def __init__(self,delay):
        threading.Thread.__init__(self)
        self.delay = delay

    def run(self):
        while True:
            APP=get_applist()
            if APP is not None and len(APP) > 1:
                for name in APP:
                    get_application(name)
            time.sleep(self.delay)
try:
    # get info from server every 30 seconds
    thread = CacheThread(30)
    thread.setDaemon(True)
    thread.start()
except:
    print 'exception'

