# Copyright 2012 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

from tempest.api.sgs import base
from tempest import test
from tempest.common import waiters
from oslo_log import log as logging
LOG = logging.getLogger(__name__)

class SGSVolumeActions(base.BaseSGSTest):
    VOLUME_FIELDS = ('id', 'name')

    @classmethod
    def setup_clients(cls):
        super(SGSVolumeActions, cls).setup_clients()
        cls.client = cls.sgs_volume_client
        cls.volumes_client = cls.volumes_client

    @classmethod
    def resource_setup(cls):
        super(SGSVolumeActions, cls).resource_setup()
        cls.name = cls.VOLUME_FIELDS[1]
        cls.volume_id_list = cls.volume_id_list
        cls.dr_volume_id_list = cls.dr_volume_id_list


    @classmethod
    def resource_cleanup(cls):
        super(SGSVolumeActions, cls).resource_cleanup()


    @test.attr(type='smoke')
    def test_enable_disable_volume(self):
        # Enable sg service of a volume
        # Then Disable the sg service
        volumes = []
        volumes.extend(self.volume_id_list)
        volumes.extend(self.dr_volume_id_list)
        for volume_id in volumes:
            LOG.info("enable volume id:%s" %(volume_id))
            self.client.enable_volume(volume_id)
            waiters.wait_for_volume_status(self.client, volume_id,
                                           'enabled')
        for volume_id in volumes:
            LOG.info("disable volume id:%s" % (volume_id))
            self.client.disable_volume(volume_id)
            waiters.wait_for_volume_status(self.volumes_client, volume_id,
                                           'available')
