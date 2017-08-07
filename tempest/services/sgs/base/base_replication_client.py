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

from oslo_serialization import jsonutils as json
import six
from six.moves.urllib import parse as urllib

from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest import config
CONF = config.CONF


class BaseSGSReplicationsClient(rest_client.RestClient):
    """Base client class to send SGS API requests"""

    exp_resp = [200, 202]

    def __init__(self, auth_provider,service, region, **kwargs):
        if 'build_timeout' not in kwargs:
            kwargs['build_timeout'] = CONF.sgs.build_timeout
        if 'build_interval' not in kwargs:
            kwargs['build_interval'] = CONF.sgs.build_interval
        super(BaseSGSReplicationsClient, self).__init__(
            auth_provider, service, region, **kwargs)

    def _prepare_params(self, params):
        """Prepares params for use in get or _ext_get methods.

        If params is a string it will be left as it is, but if it's not it will
        be urlencoded.
        """
        if isinstance(params, six.string_types):
            return params
        return urllib.urlencode(params)

    def list_replications(self, detail=False, params=None):
        """List all the volumes created.

        Params can be a string (must be urlencoded) or a dictionary.
        """
        url = 'replications'
        if detail:
            url += '/detail'
        if params:
            url += '?%s' % self._prepare_params(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(self.exp_resp, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_replication(self, master_vol, slave_vol, **kwargs):
        """Create replication pair with volumes."""
        kwargs['master_volume'] = master_vol
        kwargs['slave_volume'] = slave_vol
        action_body = {"replication": kwargs}
        url = "/replications"
        resp, body = self.post(url,json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(self.exp_resp, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_replication(self, replication_id):
        """Returns the details of a single replication."""
        url = "replications/%s" % str(replication_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(self.exp_resp, resp.status)
        return rest_client.ResponseBody(resp, body)

    def enable_replication(self, replication_id, **kwargs):
        """Enable replication"""
        action_body = {"enable": kwargs}
        url = "replications/%s/action" % str(replication_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(self.exp_resp, resp.status)
        return rest_client.ResponseBody(resp, body)

    def disable_replication(self, replication_id):
        """Disable replication"""
        action_body = {"disable": None}
        url = "replications/%s/action" % str(replication_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(self.exp_resp, resp.status)
        return rest_client.ResponseBody(resp, body)

    def failover_replication(self, replication_id, force=False):
        """Failover replication"""
        action_body = {"failover": {
            'force': force
        }}
        url = "replications/%s/action" % str(replication_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(self.exp_resp, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reverse_replication(self, replication_id):
        """Reverse replication"""
        action_body = {"reverse": None}
        url = "replications/%s/action" % str(replication_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(self.exp_resp, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_replication(self, replication_id):
        """Delete the specified replication"""
        resp, body = self.delete("replications/%s" % str(replication_id))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reset_state(self,replication_id,state):
        """Reset replication state"""
        action_body = {"status": state}
        url = "replications/%s/action" % str(replication_id)
        resp, body = self.post(url, json.dumps(action_body))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_replication(id)
        except lib_exc.NotFound:
            return True
        return False