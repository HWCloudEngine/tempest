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
        cls.local_test_vm_id = cls.local_test_vm_id
        cls.replication_test_vm_id = cls.replication_test_vm_id

    @classmethod
    def resource_cleanup(cls):
        super(SGSVolumeActions, cls).resource_cleanup()

    def setUp(self):
        super(SGSVolumeActions, self).setUp()
        self.local_volume_id_list = []
        self.replication_volume_id_list = []
        self.volume_id_list = []
        test_volume_count = 1
        for i in range(test_volume_count):
            volume = self.create_local_volume()
            self.local_volume_id_list.append(volume['id'])
            self.volume_id_list.append(volume['id'])
            LOG.info("@@@in setUp,creat volume:%s " % (volume['id']))
            rep_volume = self.create_replication_volume()
            self.replication_volume_id_list.append(rep_volume['id'])
            self.volume_id_list.append(rep_volume['id'])
            LOG.info("@@@in setUp,creat volume:%s " %(rep_volume['id']))

    def tearDown(self):
        LOG.info("@@@call tearDown")
        for volume_id in self.local_volume_id_list:
            if self.sgs_volume_client.is_resource_deleted(volume_id):
                continue
            body = self.sgs_volume_client.show_volume(volume_id)['volume']
            volume_status = body['status']
            if volume_status == 'in-use':
                self.sgs_volume_client.detach_volume(self.local_test_vm_id,volume_id)
                waiters.wait_for_volume_status(self.sgs_volume_client, volume_id,
                                               'enabled')
                LOG.info("@@@tearDown, detach volume:%s" %(volume_id))
        for volume_id in self.replication_volume_id_list:
            if self.sgs_volume_client.is_resource_deleted(volume_id):
                continue
            body = self.sgs_volume_client.show_volume(volume_id)['volume']
            volume_status = body['status']
            if volume_status == 'in-use':
                self.sgs_volume_client.detach_volume(self.replication_test_vm_id,volume_id)
                waiters.wait_for_volume_status(self.sgs_volume_client, volume_id,
                                               'enabled')
                LOG.info("@@@tearDown, detach volume:%s" % (volume_id))

        for volume_id in self.volume_id_list:
            if self.sgs_volume_client.is_resource_deleted(volume_id) == False:
                body = self.sgs_volume_client.show_volume(volume_id)['volume']
                volume_status = body['status']
                LOG.info("@@@try destory sg volume:%s,status:%s" % (volume_id, volume_status))
                if volume_status == 'enabled':
                    self.sgs_volume_client.disable_volume(volume_id)
                    waiters.wait_for_volume_status(self.volumes_client, volume_id,
                                                   'available')
                    LOG.info("@@@tearDown, disable volume:%s" % (volume_id))
            self.volumes_client.delete_volume(volume_id)
            self.volumes_client.wait_for_resource_deletion(volume_id)
            LOG.info("@@@tearDown, delete volume:%s" % (volume_id))
        super(SGSVolumeActions, self).tearDown()

    @test.attr(type='sgs-smoke')
    def test_enable_disable_volume(self):
        # Enable sg service of a volume
        # Then Disable the sg service
        for volume_id in self.volume_id_list:
            LOG.info("@@@enable volume id:%s" %(volume_id))
            self.client.enable_volume(volume_id)
            waiters.wait_for_volume_status(self.client, volume_id,
                                           'enabled')
        for volume_id in self.volume_id_list:
            LOG.info("@@@disable volume id:%s" % (volume_id))
            self.client.disable_volume(volume_id)
            waiters.wait_for_volume_status(self.volumes_client, volume_id,
                                           'available')

    @test.attr(type='sgs-smoke')
    def test_enable_attach_detach_disable_volume(self):
        """ Enable  sg service of a volume
        Attach sg volume to a instance
        Detach the sg volume
        Then Disable the sg service """
        for volume_id in self.volume_id_list:
            LOG.info("@@@enable volume id:%s" % (volume_id))
            self.client.enable_volume(volume_id)
            waiters.wait_for_volume_status(self.client, volume_id,
                                           'enabled')

        for local_volume_id in self.local_volume_id_list:
            LOG.info("@@@attach volume id:%s" % (local_volume_id))
            self.client.attach_volume(self.local_test_vm_id,local_volume_id)
            waiters.wait_for_volume_status(self.client, local_volume_id,
                                           'in-use')

        for rep_volume_id in self.replication_volume_id_list:
            LOG.info("@@@attach volume id:%s" % (rep_volume_id))
            self.client.attach_volume(self.replication_test_vm_id,rep_volume_id)
            waiters.wait_for_volume_status(self.client, rep_volume_id,
                                           'in-use')

        for local_volume_id in self.local_volume_id_list:
            LOG.info("@@@detach volume id:%s" % (local_volume_id))
            self.client.detach_volume(self.local_test_vm_id,local_volume_id)
            waiters.wait_for_volume_status(self.client, local_volume_id,
                                           'enabled')

        for rep_volume_id in self.replication_volume_id_list:
            LOG.info("@@@detach volume id:%s" % (rep_volume_id))
            self.client.detach_volume(self.replication_test_vm_id,rep_volume_id)
            waiters.wait_for_volume_status(self.client, rep_volume_id,
                                           'enabled')

        for volume_id in self.volume_id_list:
            LOG.info("@@@disable volume id:%s" % (volume_id))
            self.client.disable_volume(volume_id)
            waiters.wait_for_volume_status(self.volumes_client, volume_id,
                                           'available')
