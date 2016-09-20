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
import time
from heat.common.i18n import _
from heat.common import timeutils as iso8601utils
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from heat.engine import resource
from heat.engine import scheduler
from oslo_log import log as logging
#from heat.openstack.common import log as logging
from eventlet import greenthread
import os

LOG = logging.getLogger(__name__)

KUBERNETES_INSTALLED = False

RC_SEP = '->'

# conditionally import so tests can work without having the dependency
# satisfied
try:
    import kubernetes
    from kubernetes import KubernetesError
    KUBERNETES_INSTALLED = True
except ImportError:
    kubernetes = None


class KubernetesReplicationController(resource.Resource):

    PROPERTIES = (
        KUBERNETES_ENDPOINT, DEFINITION, NAME, APIVERSION, NAMESPACE,
        TOKEN, ROLLING_UPDATES
    ) = (
        'kubernetes_endpoint', 'definition', 'name',
        'apiversion', 'namespace', 'token',
        'rolling_updates'
    )

    _ROLLING_UPDATES_SCHEMA = (
        PAUSE_TIME, BATCH_PERCENTAGE
    ) = (
        'pause_time', 'batch_percentage'
    )

    properties_schema = {
        KUBERNETES_ENDPOINT: properties.Schema(
            properties.Schema.STRING,
            _('Kubernetes daemon endpoint (by default the local kubernetes daemon '
              'will be used).'),
            default='http://127.0.0.1:8080',
            update_allowed=True
        ),
        DEFINITION: properties.Schema(
            properties.Schema.MAP,
            _('Content of the defintion of ReplicationController.'),
            required=True,
            update_allowed=True
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the container.'),
            update_allowed=True
        ),
        APIVERSION: properties.Schema(
            properties.Schema.STRING,
            _('API Version of Kubernetes, by default is v1.'),
            default='v1',
            update_allowed=True
        ),
        NAMESPACE: properties.Schema(
            properties.Schema.STRING,
            _('Namespace of current ReplicationController, default is default.'),
            required=True
        ),
        TOKEN: properties.Schema(
            properties.Schema.STRING,
            _('The token by using SSL.'),
            required=True,
            update_allowed=True
        ),
        ROLLING_UPDATES: properties.Schema(
            properties.Schema.MAP,
            _('Policy for rolling updates for this scaling group.'),
            update_allowed=True,
            schema={
                PAUSE_TIME: properties.Schema(
                    properties.Schema.INTEGER,
                    _('The seconds to wait between batches of updates, '
                      'should be no more than a month.'),
                    constraints=[constraints.Range(min=0, max=2592000)],
                    default=0),
                BATCH_PERCENTAGE: properties.Schema(
                    properties.Schema.INTEGER,
                    _('The percentage of Pods to rolling update one time.'),
                    constraints=[constraints.Range(min=1, max=100)],
                    default=30)
            },
        ),
    }

    def __init__(self, name, definition, stack):
        super(KubernetesReplicationController, self).__init__(name, definition, stack)
        self.update_policy = self.properties.get(self.ROLLING_UPDATES)
        self.update_list = []

        self._init_config()

    def _init_config(self):
        os.sys.path.append(os.path.expanduser("~/.paas/"))
        try:
            import heat_plugin_config as config
        except ImportError:
            config = None

        if not config or 'upd_pod_node_schedule_pause' not in dir(config):
            self.upd_pod_node_schedule_pause = 0
        else:
            self.upd_pod_node_schedule_pause = config.upd_pod_node_schedule_pause

        if not config or 'pod_fail_node_schedule_pause' not in dir(config):
            self.pod_fail_node_schedule_pause = 60
        else:
            self.pod_fail_node_schedule_pause = config.pod_fail_node_schedule_pause

        if not config or 'pod_waiting_timeout' not in dir(config):
            self.pod_waiting_timeout = 90
        else:
            self.pod_waiting_timeout = config.pod_fail_node_schedule_pause

    def get_client(self, http_header=None):
        client = None
        if KUBERNETES_INSTALLED:
            base_url = ('%s/api/%s' %
                        (self.properties.get(self.KUBERNETES_ENDPOINT),
                         self.properties.get("v1" if self.APIVERSION == "v1beta3" else self.APIVERSION)))
            client = kubernetes.Api(base_url=base_url,
                                    request_headers=http_header,
                                    token=self.properties.get(self.TOKEN, None))
        return client

    def _resolve_attribute(self, name):
        if not self.resource_id:
            return

    def _is_pod_running(self, pod):
        if pod.Status.Phase == "Running":
            return self._is_pod_ready(pod)
        return False

    def _is_pod_ready(self, pod):
        if pod.Status.Conditions:
            for val in pod.Status.Conditions:
                if val.get('type', None) == 'Ready':
                    return val.get('status') == "True"
        return False

    def __gen_new_rc(self, spec):
        spec['metadata']['name'] += 'r'

        spec['spec']['selector']['internalID'] += 'r'
        spec['metadata']['labels']['internalID'] += 'r'
        spec['spec']['template']['metadata']['labels']['internalID'] += 'r'

        return (spec['metadata']['name'], json.dumps(spec))

    def handle_create(self):
        fname = 'handle_create'

        client = self.get_client()
        content = json.dumps(self.properties[self.DEFINITION])
        rc_name = ""
        self.ns = self.properties[self.NAMESPACE]
        # consider for rollback case, which would have two rc exist with the
        # same name
        # check if the rc is existing
        try:
            result = client.CreateReplicationController(content, self.ns)
            rc_name = result.Name

            LOG.info(_("[%s] %s: rc <%s> is created"
                       % (self.stack.name, fname, rc_name)))
        except KubernetesError, e:
            if (type(e.message) is dict and
                    e.message['message'].find("AlreadyExists") >= 0):
                content_json = self.properties[self.DEFINITION]
                if (self.stack.status_reason in
                        ['Stack UPDATE started', 'Stack ROLLBACK started']):
                    # For those cases:
                    #    1) update from UPDATE_FAILURE
                    #    2) ROLLBACK
                    # heat will delete this RC later,
                    # so we need to create a same RC with different name.
                    rc_name, new_rc = self.__gen_new_rc(content_json)
                    client.CreateReplicationController(new_rc, self.ns)
                else:
                    # get rc name and replicas from the content, then resize it
                    rc_name = content_json['metadata']['name']
                    rc_replicas = content_json['spec']['replicas']
                    client.ResizeReplicationController(
                        name=rc_name, replicas=rc_replicas, namespace=self.ns)
            else:
                raise
        self.resource_id_set(rc_name)
        return rc_name

    # TODO: close nodes when delete stack
    # TODO: check k8s schedule interval when no resource is available
    def check_create_complete(self, rc_name):
        """
        create complete if all of the conditions are true:
            1. all pods have been created
            2. all pods are running and ready
        """

        client = self.get_client()
        #get the replicationcontroller by given name
        rc = client.GetReplicationController(name=rc_name,
                                             namespace=self.ns)
        #check whether the current state equals with desired state
        if rc.DesiredState > rc.CurrentState:
            return False
        #get all pods which are labeled by the given rc first
        pod_list = client.GetPods(namespace=self.ns,
                                  selector=rc.Spec.ReplicaSelector)
        if len(pod_list.Items) < rc.DesiredState:
            return False
        for pod in pod_list.Items:
            if not self._is_pod_running(pod):
                if self._can_reschedule_pod(pod):
                    self._reschedule_pod(client, pod)
                return False

        return True

    def handle_delete(self):
        LOG.info(_("[%s]: Start to delete rc <%s>"
                   % (self.stack.name, self.resource_id)))

        if self.resource_id is None:
            return

        rc_list = self.resource_id.split(RC_SEP)
        client = self.get_client()
        self.ns = self.properties[self.NAMESPACE]
        for rc in rc_list:
            rc_k8s = client.GetReplicationController(name=rc, namespace=self.ns)
            if rc_k8s:
                #NEED resize rc as 0 to save time
                client.ResizeReplicationController(
                    name=rc, replicas=0, namespace=self.ns)

        return rc_list

    def check_delete_complete(self, rc_list):
        if rc_list is None:
            return True

        client = self.get_client()

        for rc_name in rc_list:
            rc_k8s = client.GetReplicationController(name=rc_name,
                                                     namespace=self.ns)
            if rc_k8s:
                if rc_k8s.DesiredState > 0:
                    client.ResizeReplicationController(
                        name=rc_name, replicas=0, namespace=self.ns)
                    LOG.info(_("RC[%s] desired replicas(%d)>0, "
                               "resize and wait..."
                               % (rc_name, rc_k8s.DesiredState)))
                else:
                    if rc_k8s.CurrentState == 0:
                        client.DeleteReplicationController(name=rc_name,
                                                           namespace=self.ns)
                        LOG.info(_("RC[%s] current replicas(%d) = 0, delete RC."
                                   % (rc_name, rc_k8s.CurrentState)))
                    else:
                        LOG.info(_("RC[%s] current replicas(%d) != 0, waiting.."
                                   % (rc_name, rc_k8s.CurrentState)))
                return False
        return True

    def _generate_update_list_newrc(self, update_unit,
                                    new_desired_replicas):
        if self.new_rc_replicas == -1:
            self.new_rc_replicas = min(new_desired_replicas, update_unit)
            self.update_list.append(('new', 'create', self.new_rc_replicas))
        else:
            self.new_rc_replicas = min(new_desired_replicas,
                                       self.new_rc_replicas + update_unit)
            self.update_list.append(('new', 'resize', self.new_rc_replicas))

    def _generate_update_list_oldrc(self, update_unit):
        if self.old_rc_replicas > 0:
            self.old_rc_replicas = max(self.old_rc_replicas - update_unit, 0)
            self.update_list.append(('old', 'resize', self.old_rc_replicas))
        else:
            self.update_list.append(('old', 'delete', -1))
            self.old_rc_replicas = -1

    def _generate_update_list(self, new_rc_desired_replicas, update_unit):
        """
        Generating the resource update step list, and then the updating process
        will base on the sequence of the list
        The list format as [(type, rc_name, action, num_replicas)]
        'type': new, old
        'action': create, delete, resize
        """
        while True:
            if (self.old_rc_replicas < 0 and
                    self.new_rc_replicas >= new_rc_desired_replicas):
                break

            if self.new_rc_replicas < new_rc_desired_replicas:
                if self.old_rc_replicas <= 0:
                    update_unit = new_rc_desired_replicas - self.new_rc_replicas
                self._generate_update_list_newrc(update_unit,
                                                 new_rc_desired_replicas)
            if self.old_rc_replicas >= 0:
                # assume we have deal the case of -1
                if self.new_rc_replicas >= new_rc_desired_replicas:
                    update_unit = max(self.old_rc_replicas, update_unit)
                self._generate_update_list_oldrc(update_unit)

        #reverse the update list, so when pop in a right order
        LOG.info(_(self.update_list))
        self.update_list.reverse()

    def __gen_rc_replicas(self, client):
        '''
        @param self.resource_id:
            MUST in formate of 'config-1.1';
            Can NOT be 'config-1.1->config-1.2->config-1.3' in UPDATE case
        @param self.new_rc_name:
            the new RC name we want now which is like 'config-1.2'
        @return: 
            self.old_rc_name:     'config-1.1'
            self.old_rc_replicas: -1 (which means rc is not exist)
        '''
        self.old_rc_name = self.resource_id

        def __get_replicas(rc_name):
            rc_k8s = client.GetReplicationController(name=rc_name,
                                                     namespace=self.ns)
            if rc_k8s:
                return rc_k8s.DesiredState
            else:
                return -1

        self.old_rc_replicas = __get_replicas(self.old_rc_name)
        self.new_rc_replicas = __get_replicas(self.new_rc_name)
        LOG.info(_('Will update: %s -> %s'
                   % (self.old_rc_name, self.new_rc_name)))

    def handle_update(self, json_snippet, tmpl_diff, prop_diff):
        fname = 'handle_update'

        LOG.info(_("[%s] %s: Start updating rc <%s>"
                    % (self.stack.name, fname, self.resource_id)))

        """
        If Properties has changed, update self.properties, so we
        get the new values during any subsequent adjustment.
        """
        updater = None
        client = self.get_client()
        self.ns = self.properties[self.NAMESPACE]

        if tmpl_diff:
            if self.ROLLING_UPDATES in prop_diff:
                self.update_policy = prop_diff.get(self.ROLLING_UPDATES)

        if prop_diff:
            self.properties = json_snippet.properties(self.properties_schema,
                                                      self.context)

            # get the expected number of pods from the new json defintion of RC
            new_rc_desired_replicas, self.new_rc_name = (
                self._get_replicas_and_name_from_defintion(prop_diff[self.DEFINITION]))

            self.__gen_rc_replicas(client)

            update_unit = 1
            if self.old_rc_replicas == -1:
                # The old rc does not exist, just create the new rc.
                LOG.info(_("[%s] %s: The old rc <%s> does not exist. Start to "
                           "create the new rc <%s>"
                           % (self.stack.name, fname,
                              self.old_rc_name, self.new_rc_name)))

                self.handle_create()
                return prop_diff
            elif self.old_rc_replicas == 0:
                update_unit = new_rc_desired_replicas
            else:
                # get the update unit based on the current number of pods
                # and the given update percentage
                update_unit = (
                    self.old_rc_replicas *
                    self.update_policy[self.BATCH_PERCENTAGE] + 99) / 100

            self.update_list = []

            # the self.update_list will be generated, create the new rc first
            # and then shrink the old one
            self._generate_update_list(new_rc_desired_replicas, update_unit)
            self._try_rolling_update(prop_diff)
            updater = prop_diff

            # for deleting a update failed resource
            self.resource_id_set(
                RC_SEP.join([self.old_rc_name, self.new_rc_name]))
        return updater

    def _try_growup_newrc(self, client, prop_diff, action, num_update):
        fname = '_try_growup_newrc'

        if action is 'create':
            import copy
            dup_dict = copy.deepcopy(prop_diff[self.DEFINITION])
            content =json.dumps(self._update_replicas_into_defintion(num_update,
                                                                     dup_dict))
            result = client.CreateReplicationController(content, self.ns)
            LOG.info(_("[%s] %s: rc <%s> is created"
                       % (self.stack.name, fname, result.Name)))
        else:
            LOG.info(_("[%s] %s: Resize the new rc <%s> to <%d> replicas"
                        % (self.stack.name, fname, self.new_rc_name, num_update)))
            client.ResizeReplicationController(name=self.new_rc_name,
                                               replicas=num_update,
                                               namespace=self.ns)

    def _try_shrink_oldrc(self, client, action, num_update):
        fname = '_try_shrink_oldrc'

        if action is 'resize':
            LOG.info(_("[%s] %s: Resize the rc <%s> to <%d> replicas."
                        % (self.stack.name, fname,
                           self.old_rc_name, num_update)))

            node_list_before = self._get_nodes_of_rc(client,
                                                     rc_name=self.old_rc_name)

            client.ResizeReplicationController(name=self.old_rc_name,
                                               replicas=num_update,
                                               namespace=self.ns)

            # maybe the following sleep is not necessary
            greenthread.sleep(5)

            node_list_after = self._get_nodes_of_rc(client,
                                                    rc_name=self.old_rc_name)

            node_list = list(set(node_list_before) - set(node_list_after))

            if self.upd_pod_node_schedule_pause > 0:
                # mark all nodes unscheduable for all deleted pods
                for node in node_list:
                    if self._close_nodes([node]):
                        LOG.info("[%s] %s: node <%s> is marked as unschedulable"
                                 % (self.stack.name, fname, node))
                    else:
                        LOG.warn("[%s] %s: node <%s> can not be marked as unschedulable"
                                 % (self.stack.name, fname, node))
                greenthread.spawn_after(self.upd_pod_node_schedule_pause,
                                        self._open_nodes, node_list)

            self._pause_between_batch()
        else:
            LOG.info(_("[%s] %s: Delete the rc <%s>"
                        % (self.stack.name, fname, self.old_rc_name)))
            client.DeleteReplicationController(name=self.old_rc_name,
                                               namespace=self.ns)

    def _check_rc_complete(self, client, rcname):
        if client.GetReplicationController(name=rcname,
                                           namespace=self.ns):
            if not self.check_create_complete(rcname):
                return False
        return True

    def _has_incomplete_update_process(self, client):
        # only check the new RC, we allow some incomplete state of old rc 
        # to accelerate the process of update
        if self._check_rc_complete(client, self.new_rc_name):
            return False
        return True

    def _pause_between_batch(self):
        def pause():
            while True:
                try:
                    yield
                except scheduler.Timeout:
                    return

        policy = self.update_policy
        pause_sec = policy[self.PAUSE_TIME]
        if pause_sec > 0:
            waiter = scheduler.TaskRunner(pause)
            waiter(timeout=pause_sec)

    def _try_rolling_update(self, prop_diff):
        client = self.get_client()
        if self._has_incomplete_update_process(client):
            return
        if len(self.update_list):
            (type_str, action_str, num_update) = self.update_list.pop()

            if type_str is "new":
                self._try_growup_newrc(client, prop_diff, action_str, num_update)
            else:
                self._try_shrink_oldrc(client, action_str, num_update)

    def check_update_complete(self, updater):
        if not updater:
            return True

        client = self.get_client()
        self._try_rolling_update(updater)
        # the update should be marked as completed only when oldrc is not
        # existing and the newrc replicas up to the desired value
        if len(self.update_list) == 0:
            if not self._has_incomplete_update_process(client):
                if not client.GetReplicationController(name=self.old_rc_name,
                                                       namespace=self.ns):
                    self.resource_id_set(self.new_rc_name)
                    return True
        return False

    def _get_replicas_and_name_from_defintion(self, content_json):
        return (content_json['spec']['replicas'], content_json['metadata']['name'])

    def _update_replicas_into_defintion(self, replicas, def_dict):
        def_dict['spec']['replicas'] = replicas
        return def_dict

    def _get_pods_of_rc(self, client, rc_name):
        rc = client.GetReplicationController(name=rc_name, namespace=self.ns)
        if not rc:
            return None

        pod_list = client.GetPods(namespace=self.ns,
                                  selector=rc.Spec.ReplicaSelector)
        if not pod_list or len(pod_list.Items) == 0:
            return None

        return pod_list.Items

    def _get_nodes_of_rc(self,  client, rc_name):
        '''
            Get all nodes of all pods in the rc
        '''
        node_list = []
        pod_list = self._get_pods_of_rc(client, rc_name)
        if pod_list is None:
            return node_list

        for pod in pod_list:
            if pod.NodeName is not None:
                node_list.append(pod.NodeName)

        return node_list

    def _get_pod_start_time(self, pod):
        try:
            return time.strptime(pod.Status.StartTime, '%Y-%m-%dT%H:%M:%SZ')
        except:
            return None

    def _get_pod_waiting_reasons(self, pod):
        reasons = []
        if pod.Status.ContainerStatuses:
            for container_status in pod.Status.ContainerStatuses:
                if 'state' in container_status and \
                    'waiting' in container_status['state'] and \
                    'reason' in container_status['state']['waiting']:
                   reasons.append(container_status['state']['waiting']['reason'])

        if len(reasons) > 0:
            return reasons
        else:
            return None

    def _can_reschedule_pod(self, pod):
        fname = "_can_reschedule_pod"

        # If the pod has not been scheduled to any node
        # do nothing.
        if not pod.NodeName:
            return False;

        if pod.Status.Phase == 'Running':
            return False

        if pod.Status.Phase == 'Failed':
            LOG.warn("[%s] %s: pod <%s>'s status is failed on node <%s>"
                % (fname, self.stack.name, pod.Name, pod.NodeName))
            return True

        if pod.Status.Phase == 'Succeeded':
            return False

        if pod.Status.Phase == 'Pending':
            waiting_reasons = self._get_pod_waiting_reasons(pod)
            if waiting_reasons:
                # container is in waiting status and
                # container can not be started due to docker API error
                for reason in waiting_reasons:
                    if 'API error' in reason:
                        LOG.warn("[%s] %s: pod <%s> meets API error, reason=\"%s\""
                            % (fname, self.stack.name, pod.Name, reason))
                        return True;

            # start_time meaning:
            # RFC 3339 date and time at which the object
            # was acknowledged by the Kubelet. This is before the Kubelet
            # pulled the container image(s) for the pod.
            start_time = self._get_pod_start_time(pod)
            if start_time and time.mktime(time.gmtime()) - time.mktime(start_time) >= self.pod_waiting_timeout:
                LOG.warn("[%s] %s: pod <%s> starts timedout in node <%s>"
                    % (fname, self.stack.name, pod.Name, pod.NodeName))
                return True

        return False

    def _set_node_schedulable_status(self, client, node, is_schedulable):
        '''
        Do not call this function directly, call _open_nodes() or
        _close_nodes() instead.
        '''
        fname = "_set_node_schedulable_status"
        ret = False
        err_msg = ""
        for i in range(5):
            try:
                client.SetNodeSchedulable(node, is_schedulable)
            except KubernetesError, e:
                err_msg = e.message
                greenthread.sleep(2)
                continue

            ret = True
            break

        if ret:
            LOG.info("[%s] %s: successfully set node <%s> as %s"
                    % (fname, self.stack.name, node, "schedulable" if is_schedulable else "unschedulable"))
        else:
            LOG.error(_("[%s] %s: failed to set node <%s> as %s. Message=%s"
                % (fname, self.stack.name, node, "schedulable" if is_schedulable else "unschedulable", err_msg)))
        return ret

    def _close_nodes(self, node_list):
        ''' set the nodes unschedulable '''

        fname = "_close_nodes"
        client = self.get_client(http_header={"Content-Type": "application/merge-patch+json"})

        ret = True
        for node in node_list:
            if not self._set_node_schedulable_status(client, node, False):
                ret = False

        return ret

    def _open_nodes(self, node_list):
        ''' set the nodes schedulable '''

        fname = "_open_nodes"
        client = self.get_client(http_header={"Content-Type": "application/merge-patch+json"})

        ret = True
        for node in node_list:
            if not self._set_node_schedulable_status(client, node, True):
                ret = False

        return ret

    def _reschedule_pod(self, client, pod):
        '''
        Reschedule the pod by marking the node to be unscheduable
        and delete the pod
        '''
        fname = "_reschedule_pod"
        if pod.NodeName:
            if not self._close_nodes([pod.NodeName]):
                return False

            LOG.warn(_("[%s] %s: node <%s> is marked to unscheduable"
                % (fname, self.stack.name, pod.NodeName)))
            gthread = greenthread.spawn_after(self.pod_fail_node_schedule_pause, self._open_nodes, [pod.NodeName])

            try:
                client.DeletePods(pod.Name, namespace=self.ns)
            except KubernetesError, e:
                LOG.warn(_("[%s] %s: failed to delete pod <%s>"
                    % (fname, self.stack.name, pod.Name)))
                return False

            LOG.warn(_("[%s] %s: pod <%s> on host <%s> is rescheduled"
                % (fname, self.stack.name, pod.Name, pod.NodeName)))
        return True; 

def resource_mapping():
    return {
        'GoogleInc::Kubernetes::ReplicationController': KubernetesReplicationController,
    }

def available_resource_mapping():
    if KUBERNETES_INSTALLED:
        return resource_mapping()
    else:
        LOG.warn(_("Kubernetes plug-in loaded, but kubernetes lib not installed."))
        return {}
