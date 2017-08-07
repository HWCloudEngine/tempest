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
from tempest.common.utils import data_utils
from tempest.lib.common import rest_client
from tempest.lib import exceptions as lib_exc
from tempest import config

CONF = config.CONF


class BaseSGSCheckpointsClient(rest_client.RestClient):
    """Base client class to send SGS API requests"""

    create_resp = 200

    def __init__(self, auth_provider, service, region, **kwargs):
        if 'build_timeout' not in kwargs:
            kwargs['build_timeout'] = CONF.sgs.build_timeout
        if 'build_interval' not in kwargs:
            kwargs['build_interval'] = CONF.sgs.build_interval
        super(BaseSGSCheckpointsClient, self).__init__(
            auth_provider, service, region, **kwargs)

    def _prepare_params(self, params):
        """Prepares params for use in get or _ext_get methods.
        If params is a string it will be left as it is, but if it's not it will
        be urlencoded.
        """
        if isinstance(params, six.string_types):
            return params
        return urllib.urlencode(params)

    def create_checkpoint(self, replication_id, **kwargs):
        """
        Create checkpoint
        name:
        description:
        """
        kwargs['replication_id'] = replication_id
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name("tempest-checkpoint-")
        action_body = {"create": kwargs}
        url = "checkpoints"
        resp, body = self.post(url,json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def list_checkpoints(self, detail=False, params=None):
        """Lists all checkpoints.

        :param detailed: Whether to return detailed checkpoint info.
        :param search_opts: Search options to filter out checkpoints.
        :param marker: Begin returning checkpoints that appear later in the
                       checkpoint list than that represented by this id.
        :param limit: Maximum number of checkpoints to return.
        :param sort_key: Key to be sorted; deprecated in kilo
        :param sort_dir: Sort direction, should be 'desc' or 'asc'; deprecated
                         in kilo
        :param sort: Sort information
        :rtype: list of :class:`Checkpoint`
        """
        url = 'checkpoints'
        if detail:
            url += '/detail'
        if params:
            url += '?%s' % self._prepare_params(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_checkpoint(self,checkpoint_id):
        """Returns the details of a single checkpoint."""
        url = "checkpoints/%s" % str(checkpoint_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_checkpoint(self, checkpoint_id, **kwargs):
        """Update checkpoint  """
        action_body = {"checkpoint": kwargs}
        url = "checkpoints/%s" % str(checkpoint_id)
        resp, body = self.put(url,json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def rollback_checkpoint(self, checkpoint_id):
        """
        rollback checkpoint
        """
        action_body = {"rollback": None}
        url = "checkpoints/%s/action" % str(checkpoint_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_checkpoint(self, checkpoint_id):
        """Delete checkpoint"""
        url = "checkpoints/%s" % str(checkpoint_id)
        resp, body = self.post(url)
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reset_state(self,checkpoint_id,state):
        """Reset checkpoint state"""
        action_body = {"status": state}
        url = "checkpoints/%s/action" % str(checkpoint_id)
        resp, body = self.post(url, json.dumps(action_body))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_checkpoint(id)
        except lib_exc.NotFound:
            return True
        return False