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


class BaseSGSVolumesClient(rest_client.RestClient):
    """Base client class to send SGS API requests"""

    create_resp = 200

    def __init__(self, auth_provider,service, region, **kwargs):
        if 'build_timeout' not in kwargs:
            kwargs['build_timeout'] = CONF.sgs.build_timeout
        if 'build_interval' not in kwargs:
            kwargs['build_interval'] = CONF.sgs.build_interval
        super(BaseSGSVolumesClient, self).__init__(
            auth_provider, service, region, **kwargs)

    def _prepare_params(self, params):
        """Prepares params for use in get or _ext_get methods.

        If params is a string it will be left as it is, but if it's not it will
        be urlencoded.
        """
        if isinstance(params, six.string_types):
            return params
        return urllib.urlencode(params)

    def list_volumes(self, detail=False, params=None):
        """List all the volumes created.

        Params can be a string (must be urlencoded) or a dictionary.
        """
        url = 'volumes'
        if detail:
            url += '/detail'
        if params:
            url += '?%s' % self._prepare_params(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_volume(self, volume_id):
        """Returns the details of a single volume."""
        url = "volumes/%s" % str(volume_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def enable_volume(self, volume_id, **kwargs):
        """Enable volume"""
        action_body = {"enable": kwargs}
        url = "volumes/%s/action" % str(volume_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def disable_volume(self, volume_id):
        """Disable volume"""
        action_body = {"disable": None}
        url = "volumes/%s/action" % str(volume_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def attach_volume(self, volume_id, instance_uuid, mode='rw'):
        """Attach volume"""
        action_body = {"attach": {
            'instance_uuid': instance_uuid,
            'mode': mode
        }}
        url = "volumes/%s/action" % str(volume_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def detach_volume(self, volume_id, instance_uuid):
        """Detach volume"""
        action_body = {'detach': {'instance_uuid': instance_uuid}}
        url = "volumes/%s/action" % str(volume_id)
        resp, body = self.post(url, json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_volume(id)
        except lib_exc.NotFound:
            return True
        return False