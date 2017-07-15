# Copyright 2012 OpenStack Foundation
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
import time
import os.path
from tempest.common import compute
from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest.lib import exceptions as lib_exc
from tempest import exceptions
import tempest.test
from oslo_log import log as logging

CONF = config.CONF

class BaseSGSTest(tempest.test.BaseTestCase):
    """Base test case class for all sgs API tests."""

    _api_version = 1
    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseSGSTest, cls).skip_checks()

        if not CONF.service_available.sgs:
            skip_msg = ("%s skipped as storage-gateway is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources()
        super(BaseSGSTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(BaseSGSTest, cls).setup_clients()
        cls.servers_client = cls.os.servers_client
        cls.security_groups_client = cls.os.compute_security_groups_client
        cls.server_groups_client = cls.os.server_groups_client
        cls.flavors_client = cls.os.flavors_client
        cls.compute_images_client = cls.os.compute_images_client
        cls.floating_ip_pools_client = cls.os.floating_ip_pools_client
        cls.floating_ips_client = cls.os.compute_floating_ips_client
        cls.keypairs_client = cls.os.keypairs_client

        cls.availability_zone_client = cls.os.availability_zone_client
        cls.sgs_volume_client = cls.os.sgs_volume_client
        if CONF.volume_feature_enabled.api_v1:
            cls.volumes_client = cls.os.volumes_client
        else:
            cls.volumes_client = cls.os.volumes_v2_client

    @classmethod
    def resource_setup(cls):
        super(BaseSGSTest, cls).resource_setup()
        cls.servers = []
        cls.volumes = []
        cls.dr_servers = []
        cls.dr_volumes = []
        cls.keypairs = []
        cls.pro_test_vm_id = CONF.sgs.test_vm_id
        cls.dr_test_vm_id = CONF.sgs.replication_test_vm_id

        if cls._api_version == 1:
            # Special fields and resp code for cinder v1
            cls.special_fields = {'name_field': 'display_name',
                                  'descrip_field': 'display_description'}
        else:
            # Special fields and resp code for cinder v2
            cls.special_fields = {'name_field': 'name',
                                  'descrip_field': 'description'}
        # Create 1 test volumes in both pro and dr site
        test_volume_count = 1
        cls.production_zone = CONF.sgs.availability_zone
        cls.volume_id_list = []
        cls.metadata = {'Type': 'work'}
        for i in range(test_volume_count):
            volume = cls.create_volume(metadata=cls.metadata, availability_zone=cls.production_zone)
            volume = cls.volumes_client.show_volume(volume['id'])['volume']
            cls.volumes.append(volume)
            cls.volume_id_list.append(volume['id'])

        cls.replication_zone = CONF.sgs.replication_availability_zone
        cls.dr_volume_id_list = []
        for i in range(test_volume_count):
            volume = cls.create_volume(metadata=cls.metadata, availability_zone=cls.replication_zone)
            volume = cls.volumes_client.show_volume(volume['id'])['volume']
            cls.dr_volumes.append(volume)
            cls.dr_volume_id_list.append(volume['id'])


    @classmethod
    def resource_cleanup(cls):
        super(BaseSGSTest, cls).resource_cleanup()
 #       cls.clear_servers()
        cls.clear_volumes()
        cls.clear_keypairs()


    @classmethod
    def clear_volumes(cls):
        volumes = []
        volumes.extend(cls.volumes)
        volumes.extend(cls.dr_volumes)
        for volume in volumes:
            try:
                cls.volumes_client.delete_volume(volume['id'])
            except Exception:
                pass

        for volume in volumes:
            try:
                cls.volumes_client.wait_for_resource_deletion(volume['id'])
            except Exception:
                pass

    @classmethod
    def clear_keypairs(cls):
        for keypair in cls.keypairs:
            try:
                cls.keypairs_client.delete_keypair(keypair)
            except Exception:
                pass

    @classmethod
    def clear_servers(cls):
        servers = []
        servers.extend(cls.servers)
        servers.extend(cls.dr_servers)
        LOG.debug('Clearing servers: %s', ','.join(
            server['id'] for server in servers))
        for server in servers:
            try:
                cls.servers_client.delete_server(server['id'])
            except lib_exc.NotFound:
                # Something else already cleaned up the server, nothing to be
                # worried about
                pass
            except Exception:
                LOG.exception('Deleting server %s failed' % server['id'])

        for server in cls.servers:
            try:
                waiters.wait_for_server_termination(cls.servers_client,
                                                    server['id'])
            except Exception:
                LOG.exception('Waiting for deletion of server %s failed'
                              % server['id'])

    @classmethod
    def create_server(cls, validatable=False, volume_backed=False, **kwargs):
        tenant_network = cls.get_tenant_network()
        body, servers = compute.create_test_server(
            cls.os,
            validatable,
            validation_resources=cls.validation_resources,
            tenant_network=tenant_network,
            **kwargs)
        return body

    @classmethod
    def wait_for_server_deletion(cls, client, plan_id):
        """Waits for plan to reach deletion."""
        start_time = int(time.time())
        while True:
            try:
                client.show_plan(plan_id)['plan']
            except Exception:
                return

            if int(time.time()) - start_time >= client.build_timeout:
                raise exceptions.TimeoutException

            time.sleep(client.build_interval)

    @classmethod
    def create_volume(cls, **kwargs):
        """Wrapper utility that returns a test volume."""
        name = data_utils.rand_name('tempest-volume')

        name_field = cls.special_fields['name_field']

        kwargs[name_field] = name
        volume = cls.volumes_client.create_volume(**kwargs)['volume']

        cls.volumes.append(volume)
        waiters.wait_for_volume_status(cls.volumes_client,
                                       volume['id'], 'available')
        return volume


