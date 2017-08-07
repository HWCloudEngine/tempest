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

class BaseSGSBackupsClient(rest_client.RestClient):
    """Base client class to send SGS API requests"""

    create_resp = 200

    def __init__(self, auth_provider,service, region, **kwargs):
        if 'build_timeout' not in kwargs:
            kwargs['build_timeout'] = CONF.sgs.build_timeout
        if 'build_interval' not in kwargs:
            kwargs['build_interval'] = CONF.sgs.build_interval
        super(BaseSGSBackupsClient, self).__init__(
            auth_provider, service, region, **kwargs)

    def _prepare_params(self, params):
        """Prepares params for use in get or _ext_get methods.

        If params is a string it will be left as it is, but if it's not it will
        be urlencoded.
        """
        if isinstance(params, six.string_types):
            return params
        return urllib.urlencode(params)

    def list_backups(self, detail=False, params=None):
        """List all the backups created.

        Params can be a string (must be urlencoded) or a dictionary.
        """
        url = 'backups'
        if detail:
            url += '/detail'
        if params:
            url += '?%s' % self._prepare_params(params)

        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def create_backup(self, volume_id, **kwargs):
        """
        Create backup with volume
        type:full or incremental backup
        destination: Local or remote backup
        name:
        description:
        """
        kwargs['volume_id'] = volume_id
        if 'type' not in kwargs:
            kwargs['type'] = "full"
        if 'destination' not in kwargs:
            kwargs['destination'] = "local"
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name("tempest-backup")
        action_body = {"create": kwargs}
        url = "backups"
        resp, body = self.post(url,json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def show_backup(self, backup_id):
        """Returns the details of a single backup."""
        url = "backups/%s" % str(backup_id)
        resp, body = self.get(url)
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def update_backup(self, backup_id, **kwargs):
        """Update backup  """
        action_body = {"backup": kwargs}
        url = "backups/%s" % str(backup_id)
        resp, body = self.put(url,json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def restore_backup(self, backup_id,volume_id):
        """Restore backup  """
        kwargs = {"volume_id": volume_id}
        action_body = {"restore": kwargs}
        url = "backups/%s/action" % str(backup_id)
        resp, body = self.post(url,json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def export_record(self, backup_id):
        """Export_record """
        kwargs = {"backup_id": backup_id}
        action_body = {"export_record": kwargs}
        url = "backups/%s/action" % str(backup_id)
        resp, body = self.post(url,json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def import_record(self, backup_record):
        """Import_record  """
        kwargs = {"backup_record": backup_record}
        action_body = {"export_record": kwargs}
        url = "backups/import_record"
        resp, body = self.post(url,json.dumps(action_body))
        body = json.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body)

    def delete_backup(self, backup_id):
        """Delete backup"""
        resp, body = self.post("backups/%s" % str(backup_id))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def reset_state(self,backup_id,state):
        """Reset backup state"""
        action_body = {"status": state}
        url = "backups/%s/action" % str(backup_id)
        resp, body = self.post(url, json.dumps(action_body))
        self.expected_success(202, resp.status)
        return rest_client.ResponseBody(resp, body)

    def is_resource_deleted(self, id):
        try:
            self.show_backup(id)
        except lib_exc.NotFound:
            return True
        return False