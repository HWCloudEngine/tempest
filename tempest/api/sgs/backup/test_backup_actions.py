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
from tempest.common import sgs_waiters
from tempest.common.utils import data_utils
from tempest import test
from oslo_log import log as logging
LOG = logging.getLogger(__name__)


class SGSBackupActions(base.BaseSGSTest):
    BACKUP_FIELDS = ('id', 'name')

    @classmethod
    def setup_clients(cls):
        super(SGSBackupActions, cls).setup_clients()
        cls.client = cls.sgs_backup_client

    @classmethod
    def resource_setup(cls):
        super(SGSBackupActions, cls).resource_setup()
        cls.name = cls.BACKUP_FIELDS[1]
        cls.local_test_vm_id = cls.local_test_vm_id
        cls.test_vol_count = 1

    @classmethod
    def resource_cleanup(cls):
        super(SGSBackupActions, cls).resource_cleanup()

    def setUp(self):
        super(SGSBackupActions, self).setUp()
        self.local_volid_list = []
        LOG.info("@@@SGSBackupActions setUp")
        for i in range(self.test_vol_count):
            local_vol = self.prepare_local_sg_volumes()
            self.local_volid_list.append(local_vol['id'])

    def tearDown(self):
        LOG.info("@@@SGSBackupActions tearDown")
        for vol_id in self.local_volid_list:
            self.destroy_local_sg_volumes(vol_id)
        super(SGSBackupActions, self).tearDown()

    @test.attr(type='smoke')
    def test_create_delete_backup(self):
        for volume_id in self.local_volid_list:
            LOG.info("@@@create backup vol_id:%s" % volume_id)
            backup = self.client.create_backup(volume_id)['backup']
            sgs_waiters.wait_for_backup_status(self.client,
                                               backup['id'],
                                               'available')
            LOG.info("@@@delete backup id:%s" % (backup['id']))
            self.cleanup_backup(backup)

    @test.attr(type='smoke')
    def test_export_import_backup(self):
        for volume_id in self.local_volid_list:
            LOG.info("@@@create backup vol_id:%s" % volume_id)
            backup = self.client.create_backup(volume_id)['backup']
            sgs_waiters.wait_for_backup_status(self.client,
                                               backup['id'],
                                               'available')
            backup_record = self.client.export_record(
                    backup['id'])['backup_record']
            import_backup = self.client.import_record(backup_record)['backup']
            sgs_waiters.wait_for_backup_status(self.client,
                                               import_backup['id'],
                                               'available')
            LOG.info("@@@delete backup id:%s" % (backup['id']))
            self.cleanup_backup(backup)
            self.cleanup_backup(import_backup)

    @test.attr(type='smoke')
    def test_restore_volume_from_backup(self):
        for volume_id in self.local_volid_list:
            backup = self.client.create_backup(volume_id)['backup']
            restore = self.client.restore_backup(backup['id',
                                                        volume_id])['volume']
            sgs_waiters.wait_for_backup_status(self.client,
                                               restore['backup_id'],
                                               'available')
            self.cleanup_backup(backup)

    @test.attr(type='smoke')
    def test_backup_create_get_list_update_delete(self):
        # Create a backup
        s_name = data_utils.rand_name('for_backup')
        params = {"name": s_name}
        backup = self.client.create_backup(self.local_volid_list[0],
                                           **params)['backup']

        # Get the backup and check for some of its details
        backup_get = self.client.show_backup(
            backup['id'])['snapshot']
        self.assertEqual(self.local_volid_list[0],
                         backup_get['volume_id'],
                         "Referred volume origin mismatch")

        # Compare also with the output from the list action
        tracking_data = (backup['id'], backup['name'])
        backups_list = self.client.list_backups()['backups']
        backups_data = [(f['id'], f['name']) for f in backups_list]
        self.assertIn(tracking_data, backups_data)

        # Updates backup with new values
        new_b_name = data_utils.rand_name('new-backup')
        new_desc = 'This is the new description of backup.'
        params = {'name': new_b_name,
                  'description': new_desc}
        update_backup = self.client.update_snapshot(
            backup['id'], **params)['backup']
        # Assert response body for update_backup method
        self.assertEqual(new_b_name, update_backup['name'])
        self.assertEqual(new_desc, update_backup['description'])
        # Assert response body for show_backup method
        updated_backup = self.client.show_backup(
            backup['id'])['backup']
        self.assertEqual(new_b_name, updated_backup['name'])
        self.assertEqual(new_desc, updated_backup['description'])

        # Delete the backup
        self.cleanup_snapshot(backup)

    def cleanup_backup(self, backup):
        # Delete the backup
        self.client.delete_backup(backup['id'])
        self.client.wait_for_resource_deletion(backup['id'])
