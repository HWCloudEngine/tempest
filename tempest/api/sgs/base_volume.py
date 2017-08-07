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
from tempest.common import waiters
from oslo_log import log as logging
LOG = logging.getLogger(__name__)

class BaseSGSVolumesTest(base.BaseSGSTest):
    VOLUME_FIELDS = ('id', 'name')

    @classmethod
    def setup_clients(cls):
        super(BaseSGSVolumesTest, cls).setup_clients()
        cls.sgs_volume_client = cls.os.sgs_volume_client
        cls.sgs_replication_client = cls.os.sgs_replication_client
        cls.sgs_backup_client = cls.os.sgs_backup_client
        cls.sgs_snapshot_client = cls.os.sgs_snapshot_client
        cls.volumes_client = cls.volumes_client

    @classmethod
    def resource_setup(cls):
        super(BaseSGSVolumesTest, cls).resource_setup()
        cls.name = cls.VOLUME_FIELDS[1]
        cls.local_test_vm_id = cls.local_test_vm_id
        cls.replication_test_vm_id = cls.replication_test_vm_id

    @classmethod
    def resource_cleanup(cls):
        super(BaseSGSVolumesTest, cls).resource_cleanup()

    @classmethod
    def prepare_local_sg_volumes(cls):
        volume = cls.create_local_volume()
        volume_id = volume['id']
        LOG.info("@@@enable volume id:%s" % (volume_id))
        cls.sgs_volume_client.enable_volume(volume_id)
        waiters.wait_for_volume_status(cls.sgs_volume_client, volume_id,
                                       'enabled')
        LOG.info("@@@attach volume id:%s" % (volume_id))
        cls.sgs_volume_client.attach_volume(cls.local_test_vm_id,volume_id)
        waiters.wait_for_volume_status(cls.sgs_volume_client, volume_id,
                                       'in-use')
        return volume

    @classmethod
    def destroy_local_sg_volumes(cls,volume_id):
        body = cls.sgs_volume_client.show_volume(volume_id)['volume']
        volume_status = body['status']
        LOG.info("@@@destory sg volume:%s,status:%s" % (volume_id, volume_status))
        if volume_status == 'in-use':
            cls.sgs_volume_client.detach_volume(cls.local_test_vm_id,volume_id)
            waiters.wait_for_volume_status(cls.sgs_volume_client, volume_id,
                                           'enabled')
            cls.sgs_volume_client.disable_volume(volume_id)
            waiters.wait_for_volume_status(cls.volumes_client, volume_id,
                                           'available')
        if volume_status == 'enabled':
            cls.sgs_volume_client.disable_volume(volume_id)
            waiters.wait_for_volume_status(cls.volumes_client, volume_id,
                                           'available')
        cls.volumes_client.delete_volume(volume_id)
        cls.volumes_client.wait_for_resource_deletion(volume_id)

    @classmethod
    def prepare_replication_sg_volumes(cls):
        volume = cls.create_replication_volume()
        volume_id = volume['id']
        LOG.info("@@@enable volume id:%s" % (volume_id))
        cls.sgs_volume_client.enable_volume(volume_id)
        waiters.wait_for_volume_status(cls.sgs_volume_client, volume_id,
                                       'enabled')
        #replication volume should not be attached?
        return volume

    @classmethod
    def destroy_replication_sg_volumes(cls, volume_id):
        if cls.sgs_volume_client.is_resource_deleted(volume_id) == False:
            body = cls.sgs_volume_client.show_volume(volume_id)['volume']
            volume_status = body['status']
            LOG.info("@@@destory sg volume:%s,status:%s" % (volume_id, volume_status))
            if volume_status == 'in-use':
                cls.sgs_volume_client.detach_volume(cls.replication_test_vm_id,volume_id)
                waiters.wait_for_volume_status(cls.sgs_volume_client, volume_id,
                                               'enabled')
                cls.sgs_volume_client.disable_volume(volume_id)
                waiters.wait_for_volume_status(cls.volumes_client, volume_id,
                                               'available')
            if volume_status == 'enabled':
                cls.sgs_volume_client.disable_volume(volume_id)
                waiters.wait_for_volume_status(cls.volumes_client, volume_id,
                                               'available')
        cls.volumes_client.delete_volume(volume_id)
        cls.volumes_client.wait_for_resource_deletion(volume_id)