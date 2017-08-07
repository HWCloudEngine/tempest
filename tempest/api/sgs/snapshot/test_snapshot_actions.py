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
from tempest.common.utils import data_utils
from tempest import test
from tempest.common import waiters
from oslo_log import log as logging
LOG = logging.getLogger(__name__)


class SGSSnapshotActions(base.BaseSGSTest):
    BACKUP_FIELDS = ('id', 'name')

    @classmethod
    def setup_clients(cls):
        super(SGSSnapshotActions, cls).setup_clients()
        cls.client = cls.sgs_snapshot_client

    @classmethod
    def resource_setup(cls):
        super(SGSSnapshotActions, cls).resource_setup()
        cls.name = cls.BACKUP_FIELDS[1]
        cls.local_test_vm_id = cls.local_test_vm_id
        cls.test_vol_count = 1

    @classmethod
    def resource_cleanup(cls):
        super(SGSSnapshotActions, cls).resource_cleanup()

    def setUp(self):
        super(SGSSnapshotActions, self).setUp()
        self.local_volid_list = []
        LOG.info("@@@SGSSnapshotActions setUp")
        for i in range(self.test_vol_count):
            local_vol = self.prepare_local_sg_volumes()
            self.local_volid_list.append(local_vol['id'])

    def tearDown(self):
        LOG.info("@@@SGSSnapshotActions tearDown")
        for vol_id in self.local_volid_list:
            self.destroy_local_sg_volumes(vol_id)
        super(SGSSnapshotActions, self).tearDown()

    @test.attr(type='smoke')
    def test_create_delete_snapshot(self):
        for volume_id in self.local_volid_list:
            LOG.info("@@@create snapshot vol_id:%s" % volume_id)
            snap = self.client.create_snapshot(volume_id)['snapshot']
            waiters.wait_for_snapshot_status(self.client,
                                             snap['id'],
                                             'available')
            LOG.info("@@@delete snapshot id:%s" % (snap['id']))
            self.cleanup_snapshot(snap)

    @test.attr(type='smoke')
    def test_create_volume_from_snapshot(self):
        for volume_id in self.local_volid_list:
            snapshot = self.client.create_snapshot(volume_id)['snapshot']
            volume = self.sgs_volume_client.create_volume(
                snapshot_id=snapshot['id'])['volume']
            waiters.wait_for_volume_status(self.volumes_client,
                                           volume['id'], 'available')
            self.volumes_client.delete_volume(volume['id'])
            self.volumes_client.wait_for_resource_deletion(volume['id'])
            self.cleanup_snapshot(snapshot)

    @test.attr(type='smoke')
    def test_snapshot_create_get_list_update_delete(self):
        # Create a snapshot
        s_name = data_utils.rand_name('snap')
        params = {"name": s_name}
        snapshot = self.client.create_snapshot(self.local_volid_list[0],
                                               **params)['snapshot']

        # Get the snap and check for some of its details
        snap_get = self.client.show_snapshot(
            snapshot['id'])['snapshot']
        self.assertEqual(self.local_volid_list[0],
                         snap_get['volume_id'],
                         "Referred volume origin mismatch")

        # Compare also with the output from the list action
        tracking_data = (snapshot['id'], snapshot['name'])
        snaps_list = self.client.list_snapshots()['snapshots']
        snaps_data = [(f['id'], f['name']) for f in snaps_list]
        self.assertIn(tracking_data, snaps_data)

        # Updates snapshot with new values
        new_s_name = data_utils.rand_name('new-snap')
        new_desc = 'This is the new description of snapshot.'
        params = {'name': new_s_name,
                  'description': new_desc}
        update_snapshot = self.client.update_snapshot(
            snapshot['id'], **params)['snapshot']
        # Assert response body for update_snapshot method
        self.assertEqual(new_s_name, update_snapshot['name'])
        self.assertEqual(new_desc, update_snapshot['description'])
        # Assert response body for show_snapshot method
        updated_snapshot = self.client.show_snapshot(
            snapshot['id'])['snapshot']
        self.assertEqual(new_s_name, updated_snapshot['name'])
        self.assertEqual(new_desc, updated_snapshot['description'])

        # Delete the snapshot
        self.cleanup_snapshot(snapshot)

    def cleanup_snapshot(self, snapshot):
        # Delete the snapshot
        self.client.delete_snapshot(snapshot['id'])
        self.client.wait_for_resource_deletion(snapshot['id'])
