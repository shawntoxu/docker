from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for
import requests
import flask
import json
from copy import deepcopy
import datetime
import time
import copy
from flask_restful import Resource
import etcd
import re
import timeit
from log import LOG
from common import *
from kubernetes import KubernetesError
#from heatclient.exc import *
import acl
from heat import heat_client
from exception import *
import os


def get_rc_name_in_heat_resource2(heat_res):
    if heat_res.resource_type != 'GoogleInc::Kubernetes::ReplicationController' \
            or heat_res.physical_resource_id == "":
        #LOG.info('not rc')
        return None
    rc_names = heat_res.physical_resource_id.split('->')

    if len(rc_names) > 1:
        rc_name=rc_names[1]
    else:
        rc_name=rc_names[0]
    return {"rc_name":rc_name,"resource_status":heat_res.resource_status,"updated_time":heat_res.updated_time}


def delete_old_cache(cfile,app_name):
    #  check file has exists at first
    if os.path.isfile(cfile):
        try:
            f = open(cfile,'r+')
            f.truncate()
        except Exception,e:
            LOG.info(e.message)
        finally:
            f.close()

def write_cache(app_name,app_json=''):
    '''
    just keep one line

    :param cfile:  cache file
    :param app_name: application name
    :param app_json: application info with  pod status & update_time
    :return:
    '''
    cfile='/tmp/'+app_name
    delete_old_cache(cfile,app_name)
    try:
        f=file(cfile,"a")
        obj={"app_name":app_name}
        datalist=[]
        for i in app_json:
            rcdata=get_rc_name_in_heat_resource2(i)
            if rcdata is not None:
                datalist.append(rcdata)
        obj['data'] =datalist
        f.write(json.dumps(obj))
        f.write('\n')
        #LOG.info(datalist)
    except Exception,e:
        LOG.info(e.message)
    finally:
        f.close()
    return obj

def read_cache(app_name):
    cachefile='/tmp/'+app_name
    if os.path.isfile(cachefile):
        if os.path.getsize(cachefile)==0:
            return None
        try:
            file2=open(cachefile,"r")
            for lines in file2:
                app_data=json.loads(lines)
                if app_data['app_name'] == app_name:
                    LOG.info('using cache for [{}]'.format(app_name))
                    return app_data
                    #LOG.info(json.loads(lines))
        except Exception,e:
            LOG.info(e.message)
        finally:
            file2.close()
    return None

class Pod:
    def __init__(self, json_data):
        self.json_data = deepcopy(json_data)
        self.mem_usage = -1          # unit is MBytes
        self.mem_cache = -1          # unit is MBytes
        self.cpu_percentage = -1.0
        self.max_mem_limit = 0.0
        try:
            mem_limit_str = self.json_data['spec']['containers'][0]['resources']['limits']['memory']
            self.max_mem_limit = self.get_mem_from_str(mem_limit_str)
        except Exception, e:
            LOG.info(e)

        try:
            key = '/paas/applications/{}/pods/{}'.format(self.namespace, self.name)
            result = etcd_client.read(key).value
            tmp_json = json.loads(result)
            if int(time.time()) - tmp_json['timestamp'] <= 60:
                self.mem_usage = tmp_json['stats']['memory']['usage'] / 1024 / 1024
                self.mem_cache = tmp_json['stats']['memory']['cache'] / 1024 / 1024
                self.cpu_percentage = tmp_json['stats']['cpu']['cpu_percentage']
                if self.cpu_percentage is None:
                    self.cpu_percentage = -1.0
            else:
                LOG.warning('The record <{}>\'s timestamp <{}> is old'.format(key, tmp_json['timestamp']))
        except Exception, e:
            LOG.error(e)

    def get_mem_from_str(self, mem_str):
        ''' unit of retrurned value is Mi '''
        match = re.match('^[0-9]*', mem_str)
        if match is None:
            return 0.0
        value = float(mem_str[match.start():match.end()])
        unit = mem_str[match.end():]
        if unit == 'Gi':
            value = value * 1024.0
        if unit == 'G':
            value = value * pow(10,9) / 1024 / 1024
        if unit == 'M':
            value = value * pow(10,6) / 1024 / 1024
        if unit == 'Mi':
            pass
        if unit == 'K':
            value = value * pow(10,3) / 1024 / 1024
        if unit == 'Ki':
            value = value / 1024

        return round(value,2)

    @property
    def name(self):
        return self.json_data['metadata']['name']

    @property
    def component_name(self):
        return self.json_data['metadata']['labels']['name']

    @property
    def namespace(self):
        return self.json_data['metadata']['namespace']

    def is_ready(self):
        if self.is_running():
            if self.json_data['status']['conditions'][0]['status'] == 'True':
                return True
            return False
        else:
            return False

    def is_running(self):
        if self.status == "Running":
            return True
        return False

    @property
    def status(self):
        phase = self.json_data['status']['phase']
        if 'deletionTimestamp' in self.json_data['metadata']:
            return 'Terminating'
        elif phase == 'Pending' \
                and 'containerStatuses' in self.json_data['status'] \
                and 'waiting' in self.json_data['status']['containerStatuses'][0]['state']:
            return self.json_data['status']['containerStatuses'][0]['state']['waiting']['reason']
        else:
            return self.json_data['status']['phase']

    @property
    def host_IP(self):
        if 'nodeName' in self.json_data['spec']['containers'][0]:
            return self.json_data['spec']['containers']['nodeName']

        if 'hostIP' in  self.json_data['status']:
            return self.json_data['status']['hostIP']

        if 'nodeName' in self.json_data['spec']:
            return self.json_data['spec']['nodeName']

        return ""

    @property
    def pod_IP(self):
        if self.is_running():
            return self.json_data['status']['podIP']
        else:
            return ""

    @property
    def start_time(self):
        if self.is_running():
            return time.strptime(self.json_data['status']['startTime'], '%Y-%m-%dT%H:%M:%SZ')
        else:
            return None

    @property
    def create_time(self):
        return time.strptime(self.json_data['metadata']['creationTimestamp'], '%Y-%m-%dT%H:%M:%SZ')

    @property
    def restart_count(self):
        if self.is_running():
            return self.json_data['status']['containerStatuses'][0]['restartCount']
        else:
            return 0

    @property
    def version(self):
        try:
            return self.json_data['metadata']['labels']['version']
        except:
            return ""

    @property
    def image_ID(self):
        try:
            return self.json_data['status']['containerStatuses'][0]['containerID'][9:]
        except:
            return None

    def dump_as_dict(self):
        cur_time = time.gmtime()
        return {
            'name': self.name,
            'is_ready': self.is_ready(),
            'is_running': self.is_running(),
            'status': self.status,
            'host_IP': self.host_IP,
            'pod_IP': self.pod_IP,
            'age': self.calc_time_delta(self.create_time, cur_time),
            'version': self.version,
            'restart_count': self.restart_count,
            'max_mem_limit': self.max_mem_limit,
            'mem_usage': self.mem_usage,
            'mem_cache': self.mem_cache,
            'component_name': self.component_name,
            'cpu_percentage': self.cpu_percentage,
        }

    def calc_time_delta(self, time1, time2):
        str = ""
        delta = int(time.mktime(time2) - time.mktime(time1))
        days = delta / (3600 * 24)
        hours = delta / 3600
        mins = delta / 60
        seconds = delta
        if days > 0:
            str = "{}d".format(days)
        elif hours > 0:
            str = "{}h".format(hours)
        elif mins > 0:
            str = "{}m".format(mins)
        elif seconds > 0:
            str = "{}s".format(seconds)

        return str


class ReplicationController2:
    def __init__(self, rc_name,resource_status, updated_time,rc_json=None):
        self.rc_json = copy.deepcopy(rc_json)
        self.name = rc_name
        self.resource_status = resource_status
        self.updated_time = updated_time

        #self.rc_name = get_rc_name_in_heat_resource(stack_resource)
        if rc_json is not None:
            self.component_name = self.rc_json['metadata']['labels']['name']
        else:
            self.component_name = self.name
        if rc_json is not None:
            self.replicas = self.rc_json['spec']['replicas']
        else:
            self.replicas = 0
        self.pods = []

    def add_pods(self, pod_list):
        self.pods += pod_list

    def dump_as_dict(self):
        return {
            'name': self.name,
            'component_name': self.component_name,
            'replicas': self.replicas,
            'status': self.resource_status,
            'updated_time': self.updated_time,
            'pods': [ pod.dump_as_dict() for pod in self.pods ]
        }


class PaasApplication2:
    def __init__(self, name, stack_json, app_resource_list,
                 rc_list_json, pod_list_json):
        self.rc_list = []
        self.name = name
        self.stack_json = copy.deepcopy(stack_json)

        if app_resource_list is not None:
            pods = []

            for pod_json in pod_list_json:
                pod = Pod(pod_json)
                pods.append(pod)


            for stack_resource in app_resource_list['data']:
                rc_json = self.__find_rc_in_list(rc_list_json,stack_resource['rc_name'])
                rc = ReplicationController2(stack_resource['rc_name'],stack_resource['resource_status'],stack_resource['updated_time'],rc_json)
                selected_pods = self.__select_pods_for_rc(rc, pods)
                rc.add_pods(selected_pods)
                self.rc_list.append(rc)

    def __find_rc_in_list(self, rc_list_json, rc_name):
        for rc_json in rc_list_json:
            if rc_name == rc_json['metadata']['name']:
                return rc_json

        return None

    def __select_pods_for_rc(self, rc, pods):
        selected_pods = []
        for pod in pods:
            if pod.component_name == rc.component_name:
                selected_pods.append(pod)

        for pod in selected_pods:
            pods.remove(pod)

        return selected_pods

    def dump_as_dict(self):
        return {
            'name': self.name,
            'stack_info': self.stack_json,
            'components': [rc.dump_as_dict() for rc in self.rc_list]
        }
