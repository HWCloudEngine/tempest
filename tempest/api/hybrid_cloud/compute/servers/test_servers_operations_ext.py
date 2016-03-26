__author__ = 'Administrator'

import time

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test
import tempest.api.compute.servers.test_create_server as test_create_server
from oslo_log import log
from tempest.common import waiters
from tempest.common import compute
from tempest.api.hybrid_cloud.compute.servers.test_servers_operations import wait_for_server_termination

LOG = log.getLogger(__name__)

CONF = config.CONF

class HybridCreateAwsServersTestJSON(base.BaseV2ComputeTest):

    disk_config = 'AUTO'

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(HybridCreateAwsServersTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(HybridCreateAwsServersTestJSON, cls).setup_clients()
        cls.client = cls.servers_client
        cls.networks_client = cls.os.networks_client
        cls.subnets_client = cls.os.subnets_client

    @classmethod
    def resource_setup(cls):
        cls.set_validation_resources()
        super(HybridCreateAwsServersTestJSON, cls).resource_setup()
        cls.meta = {'hello': 'world'}
        cls.accessIPv4 = '1.1.1.1'
        cls.accessIPv6 = '0000:0000:0000:0000:0000:babe:220.12.22.2'
        cls.name = data_utils.rand_name('server')
        cls.password = data_utils.rand_password()
        disk_config = cls.disk_config

    @test.idempotent_id('12291cd8-71fc-443c-8cab-08e24114ecc9')
    def test_create_server_from_volume_to_volume(self):
        LOG.warning('az: %s' % CONF.compute.aws_availability_zone)
        kwargs = self._create_volume_from_image()
        try:
            self.create_test_server_for_bdm(wait_until="ACTIVE",
                                availability_zone=CONF.compute.aws_availability_zone,
                                **kwargs)
        except Exception, e:
            import traceback
            LOG.warning('exception: %s ' % traceback.format_exc(e))
            raise e

    @test.idempotent_id('12291cd8-71fc-443c-8cab-0522c114ecc9')
    def test_create_server_from_image_to_volume(self):
        image_id = CONF.compute.image_ref
        bd_map_v2 = []
        boot_info = {
            'uuid': image_id,
            'source_type': 'image',
            'destination_type': 'volume',
            'boot_index': 0,
            'delete_on_termination': True,
            'volume_size': 1}

        bd_map_v2.append(boot_info)
        kwargs = {}
        kwargs['block_device_mapping_v2'] = bd_map_v2
        self.create_test_server_for_bdm(wait_until="ACTIVE",
                                availability_zone=CONF.compute.aws_availability_zone,
                                **kwargs)

    @test.idempotent_id('12791ed9-71fc-443c-8cab-1372c114ecc9')
    def test_create_server_with_blank_volume(self):
        LOG.warning('az: %s' % CONF.compute.aws_availability_zone)
        kwargs = self._create_volume_from_image()
        blank_volume = self._get_blank_volume()
        kwargs['block_device_mapping_v2'].append(blank_volume)
        try:
            self.create_test_server_for_bdm(wait_until="ACTIVE",
                                availability_zone=CONF.compute.aws_availability_zone,
                                **kwargs)
        except Exception, e:
            import traceback
            LOG.warning('exception: %s ' % traceback.format_exc(e))
            raise e

    @test.idempotent_id('12291cd8-71fc-443c-8cab-0522c114ecc9')
    def test_delete_on_termination_is_true(self):
        image_id = CONF.compute.image_ref
        bd_map_v2 = []
        boot_info = {
            'uuid': image_id,
            'source_type': 'image',
            'destination_type': 'volume',
            'boot_index': 0,
            'delete_on_termination': True,
            'volume_size': 1}

        bd_map_v2.append(boot_info)
        kwargs = {}
        kwargs['block_device_mapping_v2'] = bd_map_v2
        server = self.create_test_server_for_bdm(wait_until="ACTIVE",
                                availability_zone=CONF.compute.aws_availability_zone,
                                **kwargs)
        LOG.warning('server: %s' % server)
        attached_volumes = self._get_volume(server['id'])
        LOG.warning('attached_volumes: %s' % attached_volumes)
        self._delete_server(server['id'])
        volumes_client = self.volumes_extensions_client
        for volume in attached_volumes:
            is_deleted = self._is_volume_delete_in_specified_time(volume, 60)
            self.assertEqual(True, is_deleted)

    @test.idempotent_id('12291cd8-71fc-443c-8cab-0522c114ecc9')
    def test_delete_on_termination_is_false(self):
        image_id = CONF.compute.image_ref
        bd_map_v2 = []
        boot_info = {
            'uuid': image_id,
            'source_type': 'image',
            'destination_type': 'volume',
            'boot_index': 0,
            'delete_on_termination': False,
            'volume_size': 1}

        bd_map_v2.append(boot_info)
        kwargs = {}
        kwargs['block_device_mapping_v2'] = bd_map_v2
        server = self.create_test_server_for_bdm(wait_until="ACTIVE",
                                availability_zone=CONF.compute.aws_availability_zone,
                                **kwargs)
        LOG.warning('server: %s' % server)
        attached_volumes = self._get_volume(server['id'])
        self._delete_server(server['id'])
        volumes_client = self.volumes_extensions_client
        for volume in attached_volumes:
            is_deleted = self._is_volume_delete_in_specified_time(volume, 10)
            self.assertEqual(False, is_deleted)

        def cleanup_volume():
            for volume in attached_volumes:
                volumes_client.delete_volume(volume['id'])
                volumes_client.wait_for_resource_deletion(volume['id'])
        self.addCleanup(cleanup_volume)

    def _is_volume_delete_in_specified_time(self,  volume,  timeout):
        is_deleted = False
        volumes_client = self.volumes_extensions_client
        start_time = int(time.time())
        while True:
            is_deleted = volumes_client.is_resource_deleted(volume['id'])
            LOG.warning('volume is deleted: %s' % is_deleted)
            if is_deleted:
                is_deleted = True
                break
            else:
                if int(time.time()) - start_time >= timeout:
                    LOG.warning('time out')
                    is_deleted = False
                    break
                else:
                    time.sleep(2)
                    continue

        return is_deleted

    @classmethod
    def _create_volume_from_image(cls):
        clients = cls.os
        image_id = CONF.compute.image_ref
        volume_name = data_utils.rand_name('volume')
        volumes_client = clients.volumes_v2_client
        if CONF.volume_feature_enabled.api_v1:
            volumes_client = clients.volumes_client
        volume = volumes_client.create_volume(
            display_name=volume_name,
            imageRef=image_id,
            volume_type=CONF.volume.aws_volume_type,
            availability_zone=CONF.volume.aws_availability_zone)
        waiters.wait_for_volume_status(volumes_client,
                                       volume['volume']['id'], 'available')
        LOG.warning('volume: %s' % volume)
        kwargs = {}
        boot_volume = {
            'uuid': volume['volume']['id'],
            'source_type': 'volume',
            'destination_type': 'volume',
            'boot_index': 0,
            'delete_on_termination': True,
            'volume_size': 1}
        bd_map_v2 = []
        bd_map_v2.append(boot_volume)
        kwargs['block_device_mapping_v2'] = bd_map_v2

        LOG.warning('bdm_v2: %s' % kwargs)
        return kwargs

    def _get_blank_volume(self):
        blank_volume = {
            'source_type': 'blank',
            'destination_type': 'volume',
            'volume_size': 1,
            'delete_on_termination': True,
            'boot_index': None
        }
        return blank_volume

    @classmethod
    def create_test_server_for_bdm(cls, validatable=False, volume_backed=False,
                           **kwargs):
        """Wrapper utility that returns a test server.

        This wrapper utility calls the common create test server and
        returns a test server. The purpose of this wrapper is to minimize
        the impact on the code of the tests already using this
        function.

        :param validatable: Whether the server will be pingable or sshable.
        :param volume_backed: Whether the instance is volume backed or not.
        """
        tenant_network = cls.get_tenant_network()
        body, servers = compute.create_test_server_for_bdm(
            cls.os,
            validatable,
            validation_resources=cls.validation_resources,
            tenant_network=tenant_network,
            volume_backed=volume_backed,
            image_id='',
            **kwargs)

        cls.servers.extend(servers)

        return body

    def _delete_server(self, server_id):
        LOG.warning('start to delete server')
        self.servers_client.delete_server(server_id)
        wait_for_server_termination(self.servers_client, server_id)
        LOG.warning('end to delete server')

    def _get_volume(self, server_id):
        """

        :param server_body:
         {
            "server": {
                "OS-EXT-STS:task_state": null,
                "addresses": {
                    "ci-net01": [{
                        "OS-EXT-IPS-MAC:mac_addr": "fa:16:3e:cc:0f:0b",
                        "version": 4,
                        "addr": "10.16.1.54",
                        "OS-EXT-IPS:type": "fixed"
                    }]
                },
                "links": [{
                    "href": "https://compute.az31.singapore--aws.huawei.com/v2/52957ad92b2146a0a2e2b3279cdc2c5a/servers/8a616287-5574-44c4-9d56-22a24e4c52b9",
                    "rel": "self"
                },
                {
                    "href": "https://compute.az31.singapore--aws.huawei.com/52957ad92b2146a0a2e2b3279cdc2c5a/servers/8a616287-5574-44c4-9d56-22a24e4c52b9",
                    "rel": "bookmark"
                }],
                "image": "",
                "numaOpts": 0,
                "OS-EXT-STS:vm_state": "active",
                "OS-EXT-SRV-ATTR:instance_name": "instance-000001ba",
                "OS-SRV-USG:launched_at": "2016-05-05T08:52:28.000000",
                "flavor": {
                    "id": "1",
                    "links": [{
                        "href": "https://compute.az31.singapore--aws.huawei.com/52957ad92b2146a0a2e2b3279cdc2c5a/flavors/1",
                        "rel": "bookmark"
                    }]
                },
                "id": "8a616287-5574-44c4-9d56-22a24e4c52b9",
                "security_groups": [{
                    "name": "default"
                }],
                "OS-SRV-USG:terminated_at": null,
                "user_id": "ea4393b196684c8ba907129181290e8d",
                "OS-DCF:diskConfig": "MANUAL",
                "accessIPv4": "",
                "accessIPv6": "",
                "progress": 0,
                "OS-EXT-STS:power_state": 1,
                "OS-EXT-AZ:availability_zone": "az31.singapore--aws",
                "config_drive": "",
                "status": "ACTIVE",
                "updated": "2016-05-05T08:52:28Z",
                "hostId": "EC28CFC3-2024-7605-79ED-2492C2A623C7",
                "OS-EXT-SRV-ATTR:host": "EC28CFC3-2024-7605-79ED-2492C2A623C7",
                "evsOpts": 0,
                "key_name": null,
                "vcpuAffinity": [0],
                "hyperThreadAffinity": "any",
                "OS-EXT-SRV-ATTR:hypervisor_hostname": "a",
                "name": "volume-vm01",
                "created": "2016-05-05T08:47:38Z",
                "tenant_id": "52957ad92b2146a0a2e2b3279cdc2c5a",
                "OS-EXT-SERVICE:service_state": "up",
                "os-extended-volumes:volumes_attached": [{
                    "id": "8e14de00-34b0-435c-9ab6-22257b2b2196"
                }],
                "metadata": {
                    "provider_node_id": "i-4cab93e8",
                    "is_hybrid_vm": "True"
                }
            }
        }
        :return:
        """
        server_body = self.servers_client.show_server(server_id)['server']
        #"os-extended-volumes:volumes_attached": [{"id": "8e14de00-34b0-435c-9ab6-22257b2b2196"}]
        volumes = server_body.get('os-extended-volumes:volumes_attached')

        return volumes

