from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for
import requests
import flask
from __main__ import app
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
from heatclient.exc import *
import acl
from heat import heat_client
from exception import *
from cache import  *


CPU_USAGE_TIME_SECOND = 1



def timeit_func(f):
    def timed(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        LOG.debug('func:%r took: %2.4f sec' % (f.__name__, te-ts))
        return result

    return timed

def get_rc_name_in_heat_resource(heat_res):
    rc_names = heat_res.physical_resource_id.split('->')
    if len(rc_names) > 1:
        return rc_names[1]
    else:
        return rc_names[0]

'''
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
'''


class ReplicationController:
    def __init__(self, stack_resource, rc_json=None):
        self.rc_json = copy.deepcopy(rc_json)
        self.stack_resource = stack_resource

        self.name = get_rc_name_in_heat_resource(stack_resource)
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
            'status': self.stack_resource.resource_status,
            'updated_time': self.stack_resource.updated_time,
            'pods': [ pod.dump_as_dict() for pod in self.pods ]
        }

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




class PaasApplication:
    @timeit_func
    def __init__(self, name, stack_json, stack_resource_list,
                 rc_list_json, pod_list_json):
        self.rc_list = []
        self.name = name
        self.stack_json = copy.deepcopy(stack_json)

        if stack_resource_list is not None:
            pods = []

            for pod_json in pod_list_json:
                pod = Pod(pod_json)
                pods.append(pod)


            for stack_resource in stack_resource_list:
                if stack_resource.resource_type != 'GoogleInc::Kubernetes::ReplicationController' \
                    or stack_resource.physical_resource_id == "":
                    continue
                rc_json = self.__find_rc_in_list(rc_list_json, get_rc_name_in_heat_resource(stack_resource))
                rc = ReplicationController(stack_resource, rc_json)
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

def get_application_name_list():
    stacks = heat_client.get_stack_list()
    return [ stack.stack_name for stack in stacks ]


'''
change to new method 
use cache 
by shawn 
'''
@timeit_func
def get_application(application_name, is_summary=False):
    if not is_summary:
        session = requests.session()
        url = 'http://{}:8080/api/v1/namespaces/{}/pods'.format(app.config['K8S_IP'], application_name)
        reply = session.get(url)
        pod_list_json = reply.json()['items']

        url = 'http://{}:8080/api/v1/namespaces/{}/replicationcontrollers'.format(app.config['K8S_IP'], application_name)
        reply = session.get(url)
        rc_list_json = reply.json()['items']

    try:
        print '---- step 2 -----'
        stack = heat_client.get_stack(application_name)
        #print stack
        stack_json = stack.to_dict()

        print '---- step 3 -----'
        res=read_cache(application_name)
        if res is  None:
            LOG.info(" not using cache")
            res=heat_client.get_resource_list(application_name)
            res=write_cache(application_name,res)
        LOG.info('---- step 3-init -----')

        if not is_summary:
            ''' change to PaasApplication2 '''
            paas_app = PaasApplication2(application_name, stack_json,
                                       res, rc_list_json,
                                       pod_list_json)
        else:
            paas_app = PaasApplication2(application_name, stack_json, None, None, None)
        return paas_app
    except Exception, e:
        LOG.warning(type(e))
        LOG.warning(e)
        return None

class Application(Resource):
    def get(self, application_name):
        LOG.info('Getting application <%s>' % (application_name))
        is_summary = False
        if 'summary' in request.args and request.args['summary'].upper() == 'Y':
            is_summary = True
        paas_app = get_application(application_name, is_summary)
        if paas_app:
            application_json = paas_app.dump_as_dict()
            application_json['kind'] = 'Application'

            response = flask.make_response(json.dumps(application_json))
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            return make_status_response(404, 'The application <{}> does not exist'.format(application_name))

    def delete(self, application_name):
        if not acl.check_acl('', 'Application.{}'.format(application_name), 'd'):
            LOG.warning('DELETE application<{}> is rejected'.format(application_name))
            return make_status_response(403, 'Access denied')

        LOG.info('Deleting application <%s>' % (application_name))
        try:
            heat_client.delete_stack(application_name)
        except HTTPNotFound, e:
            LOG.warning(e)
            return make_status_response(404, str(e))
        except Exception, e:
            return make_status_response(500, 'Internal error')
        else:
            return make_status_response(200)

    def options(self, application_name):
        response = flask.make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'DELETE'
        return response

class ApplicationList(Resource):
    def is_heat_template_valid(self, template):
        '''
        Check if a given template is valid or not.
        Currently it only checkes if namespace of all components are the same.
        '''
        return True

    def get(self):
        LOG.info('get ApplicationList')
        is_summary = False
        if 'summary' in request.args and request.args['summary'].upper() == 'Y':
            is_summary = True
        app_json_list = []
        try:
            names = get_application_name_list()
            #LOG.warning('debug shawn---getjson start--{}'.format(time.time()))
            for name in names:
                app_json_list.append(get_application(name, is_summary).dump_as_dict())
            #LOG.warning('debug shawn---getjson  over--{}'.format(time.time()))
        except Exception as e:
            LOG.error(e)
            return make_status_response(500, 'Internal error')

        response_json = {'kind': 'ApplicationList', 'items': app_json_list}
        response = flask.make_response(json.dumps(response_json))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    def post(self):
        ''' create an application '''
        template = request.get_json()
        if template is None:
            return make_status_response(400, 'Bad application template')

        namespace = None
        try:
            namespace = self.get_namespace_from_template(template)
        except BadAppTemplate as e:
            LOG.warning(e.message)
            return make_status_response(400, e.message)
        except Exception as e:
            LOG.warning(e.message)
            return make_status_response(400, 'Bad application template')
        finally:
            temp_file = dump_app_json_into_file(namespace, json.dumps(template, indent=2))
            LOG.info('dump template into ' + temp_file)

        try:
            # ops platform may attach a field 'token'
            template.pop('token')
        except:
            pass

        LOG.info("Creating application <%s>" % (namespace))

        stack = None
        try:
            stack = heat_client.get_stack(namespace)
        except HTTPNotFound:
            # The stack does not exist
            pass
        except Exception, e:
            return make_status_response(500, 'Internal error')

        if stack is not None:
            if not acl.check_acl('', 'Application', 'u'):
                LOG.warning('UPDATE application<{}> is rejected'.format(namespace))
                make_status_response(403, 'Access denied')
            elif stack.status != 'COMPLETE' and stack.status != 'FAILED':
                LOG.warning('UPDATE application <{}> is rejected'.format(namespace))
                return make_status_response(403, 'UPDATE application <{}> is rejected because its status is {}_{}'.format(namespace, stack.action, stack.status))
            try:
                heat_client.update_stack(namespace, template)
            except Exception as e:
                LOG.error('Failed to update stack <{}>. Error message is: {}'.format(namespace, str(e)))
                message = ''
                if 'CircularDependencyException' in str(e):
                    message = 'found Circulard Dependency'
                return make_status_response(400, message)
        else:
            try:
                heat_client.create_stack(namespace, template)
            except Exception as e:
                LOG.error('Failed to create stack <{}>. Error message is: {}'.format(namespace, str(e)))
                message = ''
                if 'CircularDependencyException' in str(e):
                    message = 'found Circulard Dependency'
                return make_status_response(400, message)
        
        return make_status_response(200)

    def get_namespace_from_template(self, template):
        namespace = None
        for res_name, res_data in template['resources'].items():
            if 'namespace' not in res_data['properties']:
                raise BadAppTemplate('namespace is not specified in resource {}'.format(res_name))
            if namespace is None:
                namespace = res_data['properties']['namespace']
            if res_data['properties']['namespace'] != namespace:
                raise BadAppTemplate('more than one namespaces are specified')
        if namespace is None:
            raise BadAppTemplate('namespace is not specified')

        return namespace

class ApplicationPod(Resource):
    def delete(self, application_name, pod_name):
        if not acl.check_acl('',application_name, 'd'):
            LOG.warning('DELETE pod<{}> of application<{}> is rejected'.format(pod_name, application_name))
            return make_status_response(403, 'Access denied')

        try:
            kube_client.DeletePods(pod_name, namespace=application_name)
        except KubernetesError, e:
            LOG.error("failed to delete pod <%s> of application <%s>" % (pod_name, application_name))
            return make_status_response(404, e.message)

        return make_status_response(200)

    def options(self, application_name, pod_name):
        response = flask.make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'DELETE'
        return response

class ApiApplicationActions(Resource):
    def post(self, app_name):
        if 'action' not in request.args or request.args['action'] != 'cancel_update':
            return make_status_response(400, 'Invalid action')

        stack = None
        try:
            if not heat_client.is_stack_existed(app_name):
                return make_status_response(404, '{} is not running'.format(app_name))
        except:
            return make_status_response(500, 'Internal error')

        try:
            heat_client.cancel_update(app_name)
        except HTTPNotFound:
            return make_status_response(404, '{} is not running'.format(app_name))
        except HTTPBadRequest:
            return make_status_response(400)
        except Exception, e:
            return make_status_response(500, 'Internal error')

        return make_status_response(200)

class ApiApplicationTemplate(Resource):
    def get(self, app_name):
        try:
            template = heat_client.get_stack_template(app_name)

            data = {
                'kind': 'ApplicationTemplate',
                'name': app_name,
                'template': template
            }

            response = flask.make_response(json.dumps(data))
            return response
        except HTTPNotFound as e:
            return make_status_response(404, 'The application <{}> is not running'.format(app_name))
        except Exception as e:
            return make_status_response(500, 'Internal error')

