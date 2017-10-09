#!/usr/bin/env python

import psutil
import os
import sys
import time
import json
from flask_restful import Resource
from flask import Flask, g
import flask
from flask_restful import Resource, Api
import sys 
import requests
import copy
import datetime
import getopt

cadvisor_IP = '127.0.0.1'
cadvisor_port = 4194
port = 12305
CPU_USAGE_TIME_SECOND = 1
node = None

class Node:
    def __init__(self, name):
        mem =  psutil.virtual_memory()
        self.name = name
        self.num_cores = psutil.cpu_count()
        self.mem_total = mem.total

    def dump_as_dict(self):
        load1, load5, load15 = os.getloadavg()
        mem =  psutil.virtual_memory()
        return {
            'name': self.name,
            'num_cores': self.num_cores,
            'mem_total': self.mem_total,
            'mem_available': mem.available,
            'load1': load1,
            'load5': load5,
            'load15': load15
        }

class ReosurcePodContainerList(Resource):
    def get(self):
        url = 'http://{}:{}/api/v1.2/docker/'.format(cadvisor_IP, cadvisor_port)
        reply = requests.get(url)
        if reply.status_code != 200:
            response = flask.make_response(json.dumps({'kind': 'Status', 'code': reply.status_code, 'message': 'kubelet error'}))
            return response

        reply_data = {}
        container_json = reply.json()
        for key, container in container_json.items():
            try:
                if 'io.kubernetes.pod.name' not in container['spec']['labels']:
                    continue
            except:
                continue
            memory_stats = container['stats'][-1]['memory']
            cpu_stats = container['stats'][-1]['cpu']
            cpu_percentage = self.parse_cpu(node.num_cores, container)
            cpu_stats['cpu_percentage'] = cpu_percentage

            container['stats'] = {
                'memory': memory_stats,
                'cpu': cpu_stats
            }
            pod_name = container['spec']['labels']['io.kubernetes.pod.name']
            namespace = container['spec']['labels']['io.kubernetes.pod.namespace']
            container['namespace'] = namespace
            container['pod_name'] = pod_name
            reply_data[os.path.basename(key)] = container

        response = flask.make_response(json.dumps(reply_data))
        return response

    def get_interval(self, cur, prev):
        '''
        return the seconds between curl and prev
        '''
        cur_date =  datetime.datetime.strptime(cur[:24], '%Y-%m-%dT%H:%M:%S.%f')
        prev_date =  datetime.datetime.strptime(prev[:24], '%Y-%m-%dT%H:%M:%S.%f')
        time_delta = cur_date - prev_date
        ret = time_delta.seconds + time_delta.microseconds / 1000000.0
        return ret

    def parse_cpu(self, core_nums, container_data):
        if (container_data['spec']['has_cpu'] and len(container_data['stats']) >= 2):
            data = container_data['stats']
            cur = data[-1]
            prev = data[-2]
            time_seconds = self.get_interval(cur['timestamp'], prev['timestamp'])
            raw_usage = cur['cpu']['usage']['total']    \
                        - prev['cpu']['usage']['total']
            usage = float(raw_usage) / pow(10,9) /time_seconds * 100
            return round(usage, 2)
        return -1

    def get_mem_from_str(self, mem_str):
        '''
        memstr = nnnGi/nnnMi
        '''
        unit = mem_str[-2:]
        if unit.upper() == 'GI':
            return float(mem_str[:-2]) * 1024
        elif unit.upper() == 'MI':
            return float(mem_str[:-2])
        elif unit.upper() == 'KI':
            return float(mem_str[:-2]) / 1024

        return -1

class ResourceNode(Resource):
    def get(self):
        response = flask.make_response(json.dumps(node.dump_as_dict()))
        return response

def usage():
    print "Usage: paas-agent.py --port=12305 --cadvisor-address=127.0.0.1:4194"

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "cadvisor-address="])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "--cadvisor-address":
            cadvisor_IP, cadvisor_port = arg.split(':')
            cadvisor_port = int(cadvisor_port)
        if opt == "--port":
            port = int(arg)
        if opt in ['-h', '--help']:
            usage()
            sys.exit(0)

    node = Node(cadvisor_IP)

    app = Flask(__name__)
    api = Api(app)
    api.add_resource(ReosurcePodContainerList, '/api/v1.0/docker')
    api.add_resource(ResourceNode, '/api/v1.0/machine')

    app.run(host="0.0.0.0", port=port, debug=True)
