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


import time

from oslo_log import log as logging

from tempest import config
from tempest import exceptions
from tempest.lib.common.utils import misc as misc_utils
from tempest.lib import exceptions as lib_exc

CONF = config.CONF
LOG = logging.getLogger(__name__)

def wait_for_sgs_replication_status(client, replication_id, status):
    """Waits for a Volume to reach a given status."""
    body = client.show_replication(replication_id)['replication']
    replication_status = body['status']
    start = int(time.time())

    while replication_status != status:
        time.sleep(client.build_interval)
        body = client.show_replication(replication_id)['replication']
        replication_status = body['status']
        if replication_status == 'error':
            raise exceptions.VolumeBuildErrorException(replication_id=replication_id)

        if int(time.time()) - start >= client.build_timeout:
            message = ('Replication %s failed to reach %s status (current %s) '
                       'within the required time (%s s).' %
                       (replication_id, status, replication_status,
                        client.build_timeout))
            raise exceptions.TimeoutException(message)