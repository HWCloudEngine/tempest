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
from tempest import config
CONF = config.CONF


class BaseSGSSnapshotsClient(rest_client.RestClient):
    """Base client class to send SGS API requests"""

    create_resp = 200

    def __init__(self, auth_provider,service, region, **kwargs):
        if 'build_timeout' not in kwargs:
            kwargs['build_timeout'] = CONF.sgs.build_timeout
        if 'build_interval' not in kwargs:
            kwargs['build_interval'] = CONF.sgs.build_interval
        super(BaseSGSSnapshotsClient, self).__init__(
            auth_provider, service, region, **kwargs)

    def _prepare_params(self, params):
        """Prepares params for use in get or _ext_get methods.
        If params is a string it will be left as it is, but if it's not it will
        be urlencoded.
        """
        if isinstance(params, six.string_types):
            return params
        return urllib.urlencode(params)

    def list_snapshots(self, detail=False, params=None):
        """List all the snapshots created.

        Params can be a string (must be urlencoded) or a dictionary.
        """
        url = 'snapshots'
        if detail:
            url += '/detail'
        if params:
            url += '?%s' % self._prepare_params(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_snapshot(self, volume_id, **kwargs):
        kwargs['volume_id'] = volume_id
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name("tempest-snapshot")
        action_body = {"create": kwargs}
        url = "/snapshots"
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_snapshot(self, snapshot_id):
        action_body = {"delete": None}
        url = "snapshots/%s/action" % str(snapshot_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def rollback_snapshot(self, snapshot_id):
        action_body = {"rollback": None}
        url = "snapshots/%s/action" % str(snapshot_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_snapshot(self, snapshot_id):
        url = "snapshots/%s" % str(snapshot_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_snapshot(self, snapshot_id, **kwargs):
        action_body = {"snapshot": kwargs}
        url = "snapshots/%s" % str(snapshot_id)
        resp, body = self.put(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)
