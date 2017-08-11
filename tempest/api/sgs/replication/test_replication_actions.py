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

from tempest.api.sgs import base_volume
from tempest import test
from tempest.common import sgs_waiters
from tempest.common import waiters
from tempest.common.utils import data_utils
from oslo_log import log as logging
LOG = logging.getLogger(__name__)

class SGSReplicationActions(base_volume.BaseSGSVolumesTest):
    VOLUME_FIELDS = ('id', 'name')

    @classmethod
    def setup_clients(cls):
        super(SGSReplicationActions, cls).setup_clients()
        cls.client = cls.sgs_replication_client
        cls.sgs_volume_client = cls.sgs_volume_client

    @classmethod
    def resource_setup(cls):
        super(SGSReplicationActions, cls).resource_setup()
        cls.name = cls.VOLUME_FIELDS[1]
        cls.local_test_vm_id = cls.local_test_vm_id
        cls.replication_test_vm_id = cls.replication_test_vm_id
        cls.test_vol_count = 1

    @classmethod
    def resource_cleanup(cls):
        super(SGSReplicationActions, cls).resource_cleanup()

    def setUp(self):
        super(SGSReplicationActions, self).setUp()
        self.local_volid_list = []
        self.replication_volid_list = []
        LOG.info("@@@setUp")
        for i in range(self.test_vol_count):
            local_vol = self.prepare_local_sg_volumes()
            self.local_volid_list.append(local_vol['id'])
            rep_vol = self.prepare_replication_sg_volumes()
            self.replication_volid_list.append(rep_vol['id'])

    def tearDown(self):
        LOG.info("@@@tearDown")
        for volid in self.local_volid_list:
            self.destroy_local_sg_volumes(volid)
        for volid in self.replication_volid_list:
            self.destroy_replication_sg_volumes(volid)
        super(SGSReplicationActions, self).tearDown()

    @test.attr(type='sgs-smoke')
    def test_create_disable_delete_replication(self):
        name = data_utils.rand_name('tempest-replication')
        master_vol = self.local_volid_list[0]
        slave_vol = self.replication_volid_list[0]
        kwargs = {
            'name':name,
            'description':'this replication is for jenkins test.',
        }
        replication = self.client.create_replication(master_vol,
                                                     slave_vol,
                                                     **kwargs)['replication']
        LOG.info("@@@create replication %s" % (replication['id']))
        sgs_waiters.wait_for_sgs_replication_status(self.client,replication['id'],'enabled')
        LOG.info("@@@disable replication %s" % (replication['id']))
        self.client.disable_replication(replication['id'])
        sgs_waiters.wait_for_sgs_replication_status(self.client, replication['id'], 'disabled')
        LOG.info("@@@delete replication %s" % (replication['id']))
        self.client.delete_replication(replication['id'])
        self.client.wait_for_resource_deletion(replication['id'])

    @test.attr(type='sgs-smoke')
    def test_create_failover_reverse_enable_disable_delete_replication(self):
        name = data_utils.rand_name('tempest-replication')
        master_vol = self.local_volid_list[0]
        slave_vol = self.replication_volid_list[0]
        kwargs = {
            'name': name,
            'description': 'this replication is for jenkins test.',
        }
        replication = self.client.create_replication(master_vol,
                                                     slave_vol,
                                                     **kwargs)['replication']
        LOG.info("@@@create replication %s" % (replication['id']))
        sgs_waiters.wait_for_sgs_replication_status(self.client, replication['id'], 'enabled')
        self.client.failover_replication(replication['id'])
        LOG.info("@@@failover replication %s" % (replication['id']))
        sgs_waiters.wait_for_sgs_replication_status(self.client, replication['id'], 'failed-over')
        self.client.reverse_replication(replication['id'])
        LOG.info("@@@reverse replication %s" % (replication['id']))
        sgs_waiters.wait_for_sgs_replication_status(self.client, replication['id'], 'disabled')
        LOG.info("@@@attach replication volume:%s" % (slave_vol))
        self.sgs_volume_client.attach_volume(self.replication_test_vm_id, slave_vol)
        LOG.info("@@@detach local volume:%s" % (master_vol))
        self.sgs_volume_client.detach_volume(self.local_test_vm_id, master_vol)
        waiters.wait_for_volume_status(self.sgs_volume_client, slave_vol, 'in-use')
        waiters.wait_for_volume_status(self.sgs_volume_client, master_vol,'enabled')
        self.client.enable_replication(replication['id'])
        LOG.info("@@@enable replication %s" % (replication['id']))
        sgs_waiters.wait_for_sgs_replication_status(self.client, replication['id'], 'enabled')
        self.client.disable_replication(replication['id'])
        LOG.info("@@@disable replication %s" % (replication['id']))
        sgs_waiters.wait_for_sgs_replication_status(self.client, replication['id'], 'disabled')
        self.client.delete_replication(replication['id'])
        LOG.info("@@@delete replication %s" % (replication['id']))
        self.client.wait_for_resource_deletion(replication['id'])