#
# Copyright (c) 2015 NDPMedia, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import six
import json

from heat.common.i18n import _
from heat.engine import attributes
from heat.engine import properties
from heat.engine import resource
from oslo_log import log as logging
#from heat.openstack.common import log as logging

LOG = logging.getLogger(__name__)

KUBERNETES_INSTALLED = False
# conditionally import so tests can work without having the dependency
# satisfied
try:
    import kubernetes
    from kubernetes import KubernetesError
    KUBERNETES_INSTALLED = True
except ImportError:
    kubernetes = None


class KubernetesService(resource.Resource):

    PROPERTIES = (
        KUBERNETES_ENDPOINT, DEFINITION,
        NAME, APIVERSION, NAMESPACE, TOKEN,
    ) = (
        'kubernetes_endpoint', 'definition',
        'name', 'apiversion', 'namespace', 'token',
    )

    #ATTRIBUTES = (
        #INFO, NETWORK_INFO, NETWORK_IP, NETWORK_GATEWAY,
        #NETWORK_TCP_PORTS, NETWORK_UDP_PORTS, LOGS, LOGS_HEAD,
        #LOGS_TAIL,
    #) = (
        #'info', 'network_info', 'network_ip', 'network_gateway',
        #'network_tcp_ports', 'network_udp_ports', 'logs', 'logs_head',
        #'logs_tail',
    #)

    properties_schema = {
        KUBERNETES_ENDPOINT: properties.Schema(
            properties.Schema.STRING,
            _('Kubernetes daemon endpoint (by default the local kubernetes daemon '
              'will be used).'),
            default='http://127.0.0.1:8080'
        ),
        DEFINITION: properties.Schema(
            properties.Schema.MAP,
            _('Location where the defintion of Service is located.'),
            default=''
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the container.'),
        ),
        APIVERSION: properties.Schema(
            properties.Schema.STRING,
            _('API Version of Kubernetes, by default is v1.'),
            default='v1'
        ),
        NAMESPACE: properties.Schema(
            properties.Schema.STRING,
            _('Namespace of current Service, default is default.'),
            default='default'
        ),
        TOKEN: properties.Schema(
            properties.Schema.STRING,
            _('The token by using SSL.'),
            default=None
        ),
    }

    #attributes_schema = {
        #LOGS: attributes.Schema(
            #_('Container logs.')
        #),
        #LOGS_HEAD: attributes.Schema(
            #_('Container first logs line.')
        #),
        #LOGS_TAIL: attributes.Schema(
            #_('Container last logs line.')
        #),
    #}

    def __init__(self, name, definition, stack):
        super(KubernetesService, self).__init__(name, definition, stack)

    def get_client(self):
        client = None
        if KUBERNETES_INSTALLED:
            base_url = ('%s/api/%s' %
                        (self.properties.get(self.KUBERNETES_ENDPOINT),
                         self.properties.get("v1" if self.APIVERSION == "v1beta3" else self.APIVERSION)))
            client = kubernetes.Api(base_url=base_url,
                                    token=self.properties.get(self.TOKEN, None))
        return client

    def _resolve_attribute(self, name):
        if not self.resource_id:
            return
        #if name == 'logs':
            #client = self.get_client()
            #logs = client.logs(self.resource_id)
            #return logs
        #if name == 'logs_head':
            #client = self.get_client()
            #logs = client.logs(self.resource_id)
            #return logs.split('\n')[0]
        #if name == 'logs_tail':
            #client = self.get_client()
            #logs = client.logs(self.resource_id)
            #return logs.split('\n').pop()

    def _read_definition(self, path):
        file_obj = open(path)
        content = None
        try:
            content = file_obj.read()
        finally:
            file_obj.close()
            return content

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        return None

    def check_update_complete(self, updater):
        return True

    def handle_create(self):
        client = self.get_client()
        service_name = ""
        self.ns = self.properties[self.NAMESPACE]
        content = json.dumps(self.properties[self.DEFINITION])
        try:
            result = client.CreateService(content, self.ns)
            service_name = result.Name
        except KubernetesError, e:
            if (type(e.message) is dict and
                    e.message['message'].find("AlreadyExists") >= 0):
                content_json = self.properties[self.DEFINITION]
                service_name = content_json['metadata']['name']
                if (self.stack.status_reason in
                        ['Stack UPDATE started', 'Stack ROLLBACK started']):
                    content_json['metadata']['name'] += '-upd'
                    service_name = content_json['metadata']['name']
                    content = json.dumps(content_json)
                    client.CreateService(content, self.ns)
            else:
                raise
        self.resource_id_set(service_name)
        return service_name

    def check_create_complete(self, service_name):
        client = self.get_client()
        service = client.GetService(name=service_name, namespace=self.ns)
        # The boolean is specified here
        if service and service.ClusterIP and service.UID:
            return True
        return False

    def handle_delete(self):
        if self.resource_id is None:
            return
        client = self.get_client()
        client.DeleteService(name=self.resource_id, namespace=self.properties[self.NAMESPACE])
        return self.resource_id

    def check_delete_complete(self, service_name):
        if service_name is None:
            return True
        client = self.get_client()
        try:
            client.GetService(name=service_name, namespace=self.properties[self.NAMESPACE])
        except KubernetesError:
            raise
        return True

def resource_mapping():
    return {
        'GoogleInc::Kubernetes::Service': KubernetesService,
    }

def available_resource_mapping():
    if KUBERNETES_INSTALLED:
        return resource_mapping()
    else:
        LOG.warn(_("Kubernetes plug-in loaded, but kubernetes lib not installed."))
        return {}
