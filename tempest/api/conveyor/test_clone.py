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

from tempest.api.conveyor import base
from tempest import test
from tempest import config
from tempest.common.utils import data_utils
import testtools
from tempest.lib import exceptions as lib_exc
import time
from tempest.common import waiters
from oslo_log import log as logging

LOG = logging.getLogger(__name__)
CONF = config.CONF


class ConveyorCloneTest(base.BaseConveyorTest):
    """Test the conveyor clone.

    Tests for  clone template and export clone template
    """

    @classmethod
    def setup_clients(cls):
        super(ConveyorCloneTest, cls).setup_clients()

    @classmethod
    def resource_setup(cls):
        super(ConveyorCloneTest, cls).resource_setup()
        cls.origin_security_group = CONF.conveyor.origin_security_group_ref
        cls.update_security_group = CONF.conveyor.update_security_group_ref
        cls.origin_net = CONF.conveyor.origin_net_ref
        cls.update_net = CONF.conveyor.update_net_ref
        cls.origin_subnet = CONF.conveyor.origin_subnet_ref
        cls.update_subnet = CONF.conveyor.update_subnet_ref
        cls.image = CONF.conveyor.image_ref
        cls.flavor = CONF.conveyor.flavor_ref
        cls.availability_zone = CONF.conveyor.availability_zone
        cls.clone_availability_zone = CONF.conveyor.clone_availability_zone
        cls.update_fix_ip = CONF.conveyor.fix_ip

        cls.meta = {'hello': 'world'}
        cls.name = data_utils.rand_name('server')
        cls.password = data_utils.rand_password()
        networks = [{'uuid': cls.origin_net}]

        key_name = data_utils.rand_name('key')
        cls.keypairs_client.create_keypair(name=key_name)
        cls.origin_keypair = key_name
        cls.keypairs.append(key_name)
        update_key_name = data_utils.rand_name('key')
        cls.keypairs_client.create_keypair(name=update_key_name)
        cls.update_keypair = update_key_name
        cls.keypairs.append(update_key_name)
        server_initial = cls.create_server(
            name=cls.name,
            image_id=cls.image,
            flavor=cls.flavor,
            networks=networks,
            wait_until='ACTIVE',
            metadata=cls.meta,
            adminPass=cls.password,
            availability_zone=cls.availability_zone)
        server = cls.servers_client.show_server(server_initial['id'])['server']

        # cls.servers_client.add_security_group(server_initial['id'],
        # name=cls.origin_security_group)
        cls.servers.append(server)
        volume_01 = cls.volumes_client.create_volume(
            size=CONF.conveyor.volume_size, display_name='test01',
            availability_zone=cls.availability_zone,
            volume_type=CONF.conveyor.volume_type)['volume']
        waiters.wait_for_volume_status(cls.volumes_client,
                                       volume_01['id'], 'available')

        cls.volumes.append(volume_01)
        volume_02 = cls.volumes_client.create_volume(
            size=CONF.conveyor.volume_size, display_name='test02',
            availability_zone=cls.availability_zone,
            volume_type=CONF.conveyor.volume_type)['volume']
        waiters.wait_for_volume_status(cls.volumes_client,
                                       volume_02['id'], 'available')

        cls.volumes.append(volume_02)

        # Attach the volume to the server
        attachment = cls.servers_client.attach_volume(
            server['id'],
            volumeId=volume_01['id'],
            device='/dev/vdb')['volumeAttachment']

        waiters.wait_for_volume_status(cls.volumes_client,
                                       volume_01['id'], 'in-use')

        # Attach the volume to the server
        attachment = cls.servers_client.attach_volume(
            server['id'],
            volumeId=volume_02['id'],
            device='/dev/vdc')['volumeAttachment']

        waiters.wait_for_volume_status(cls.volumes_client,
                                       volume_02['id'], 'in-use')

    @classmethod
    def resource_cleanup(cls):
        super(ConveyorCloneTest, cls).resource_cleanup()

    @test.attr(type='smoke')
    def test_clone_without_update_in_same_az(self):
        src_server = self.servers[0]
        init_servers = [_s['id'] for _s in self.servers]
        resources = [{"type": "OS::Nova::Server", "id": src_server['id']}]
        params = {"type": 'clone', "resources": resources}
        plan = self.conveyor_client.create_plan(**params)
        plan_id = plan.get('plan').get('plan_id')
        params_clone = {"destination": self.availability_zone,
                        "update_resources": []}
        self.conveyor_client.clone(plan_id, **params_clone)
        self.wait_for_plan_status(self.conveyor_client, plan_id, 'finished')
        time.sleep(60)
        params = {'name': src_server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        clone_servers = []
        dst_server = [s for s in servers if s['id'] not in init_servers][0]
        # self.clone_servers.append(dst_server)
        clone_servers.append(dst_server)

        body = self.servers_client.list_volume_attachments(
            dst_server['id'])['volumeAttachments']
        self.assertEqual(2, len(body))
        clone_volumes = []
        for b in body:
            clone_volme = {'id': b['volumeId']}
            # self.clone_volumes.append(clone_volme)
            clone_volumes.append(clone_volme)

        #         server_details = self.servers_client.show_server(dst_server['id'])['server']
        #
        #         resouces_fields = { "metadata" : self.meta}
        #             #"key_name" : self.origin_keypair}
        #             #"security_groups" : self.origin_security_group, }
        #
        #         for name, expected_value in resouces_fields.iteritems():
        #             self.assertEqual(expected_value, server_details[name])

        plan = self.conveyor_client.show_plan(plan_id).get('plan')
        #         stack_id = plan.get('stack_id')
        #                 # delete the stack
        #         self.orchestration_client.delete_stack(stack_id)

        self.conveyor_client.delete_plan(plan_id)

        self.clear_temp_servers(clone_servers)
        self.clear_temp_volumes(clone_volumes)

    @testtools.skip('Do not support clone in same az, need modify')
    @test.attr(type='smoke')
    def test_clone_update_fix_ip_in_same_az(self):
        src_server = self.servers[0]
        init_servers = [_s['id'] for _s in self.servers]
        resources = [{"type": "OS::Nova::Server", "id": src_server['id']}]
        params = {"type": 'clone', "resources": resources}
        plan = self.conveyor_client.create_plan(**params)
        plan_id = plan.get('plan').get('plan_id')
        update_resource = [{'res_id': 'port_0',
                            'fixed_ips': [{'subnet_id': {'get_resource': 'subnet_0'},
                                           'ip_address': self.update_fix_ip}],
                            'type': 'OS::Neutron::Port'}]
        params_clone = {"destination": self.availability_zone,
                        "update_resources": update_resource}
        self.conveyor_client.clone(plan_id, **params_clone)
        self.wait_for_plan_status(self.conveyor_client, plan_id, 'finished')
        time.sleep(60)
        params = {'ip': self.update_fix_ip}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(1, len(servers))

        params = {'name': src_server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        clone_servers = []
        dst_server = [s for s in servers if s['id'] not in init_servers][0]
        # self.clone_servers.append(dst_server)
        clone_servers.append(dst_server)

        body = self.servers_client.list_volume_attachments(
            dst_server['id'])['volumeAttachments']
        self.assertEqual(2, len(body))
        clone_volumes = []
        for b in body:
            clone_volme = {'id': b['volumeId']}
            # self.clone_volumes.append(clone_volme)
            clone_volumes.append(clone_volme)

        #         server_details = self.servers_client.show_server(dst_server['id'])['server']
        #
        #         resouces_fields = { "metadata" : self.meta}
        #             #"key_name" : self.origin_keypair}
        #             #"security_groups" : self.origin_security_group, }
        #
        #         for name, expected_value in resouces_fields.iteritems():
        #             self.assertEqual(expected_value, server_details[name])

        plan = self.conveyor_client.show_plan(plan_id).get('plan')
        #         stack_id = plan.get('stack_id')
        #                 # delete the stack
        #         self.orchestration_client.delete_stack(stack_id)

        self.conveyor_client.delete_plan(plan_id)
        self.clear_temp_servers(clone_servers)
        self.clear_temp_volumes(clone_volumes)

    @test.attr(type='smoke')
    def test_clone_update_others_in_same_az(self):
        src_server = self.servers[0]
        init_servers = [_s['id'] for _s in self.servers]
        resources = [{"type": "OS::Nova::Server", "id": src_server['id']}]
        params = {"type": 'clone', "resources": resources}
        plan = self.conveyor_client.create_plan(**params)
        plan_id = plan.get('plan').get('plan_id')
        update_resource = [{'res_id': 'network_0',
                            'id': self.update_net,
                            'type': 'OS::Neutron::Net'},
                           {'res_id': 'subnet_0',
                            'id': self.update_subnet,
                            'type': 'OS::Neutron::Subnet'},
                           #                            {'res_id': 'keypair_0',
                           #                             'id': self.update_keypair,
                           #                             'type': 'OS::Nova::KeyPair'}
                           ]
        params_clone = {"destination": self.availability_zone,
                        "update_resources": update_resource}
        self.conveyor_client.clone(plan_id, **params_clone)
        self.wait_for_plan_status(self.conveyor_client, plan_id, 'finished')
        time.sleep(60)
        params = {'name': src_server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        clone_servers = []
        dst_server = [s for s in servers if s['id'] not in init_servers][0]
        # self.clone_servers.append(dst_server)
        clone_servers.append(dst_server)

        body = self.servers_client.list_volume_attachments(
            dst_server['id'])['volumeAttachments']
        self.assertEqual(2, len(body))
        clone_volumes = []
        for b in body:
            clone_volme = {'id': b['volumeId']}
            # self.clone_volumes.append(clone_volme)
            clone_volumes.append(clone_volme)

        #         server_details = self.servers_client.show_server(dst_server['id'])['server']
        #
        #         resouces_fields = { "metadata" : self.meta}
        #             #"key_name" : self.origin_keypair}
        #             #"security_groups" : self.update_security_group, }
        #
        #         for name, expected_value in resouces_fields.iteritems():
        #             self.assertEqual(expected_value, server_details[name])

        plan = self.conveyor_client.show_plan(plan_id).get('plan')
        #         stack_id = plan.get('stack_id')
        #                 # delete the stack
        #         self.orchestration_client.delete_stack(stack_id)

        self.conveyor_client.delete_plan(plan_id)
        self.clear_temp_servers(clone_servers)
        self.clear_temp_volumes(clone_volumes)

    # @testtools.skip('Do not support clone between different az')
    @test.attr(type='smoke')
    def test_clone_without_update_in_diff_az(self):
        src_server = self.servers[0]
        init_servers = [_s['id'] for _s in self.servers]
        resources = [{"type": "OS::Nova::Server", "id": src_server['id']}]
        params = {"type": 'clone', "resources": resources}
        plan = self.conveyor_client.create_plan(**params)
        plan_id = plan.get('plan').get('plan_id')
        params_clone = {"destination": self.clone_availability_zone,
                        "update_resources": []}
        self.conveyor_client.clone(plan_id, **params_clone)
        self.wait_for_plan_status(self.conveyor_client, plan_id, 'finished')
        time.sleep(60)
        params = {'name': src_server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        clone_servers = []
        dst_server = [s for s in servers if s['id'] not in init_servers][0]
        # self.clone_servers.append(dst_server)
        clone_servers.append(dst_server)

        body = self.servers_client.list_volume_attachments(
            dst_server['id'])['volumeAttachments']
        self.assertEqual(2, len(body))
        clone_volumes = []
        for b in body:
            clone_volme = {'id': b['volumeId']}
            # self.clone_volumes.append(clone_volme)
            clone_volumes.append(clone_volme)

        #         server_details = self.servers_client.show_server(dst_server['id'])('server')
        #
        #         resouces_fields = { "metadata" : self.meta}
        #             #"key_name" : self.origin_keypair}
        #             #"security_groups" : self.origin_security_group, }
        #
        #         for name, expected_value in resouces_fields.iteritems():
        #             self.assertEqual(expected_value, server_details[name])

        plan = self.conveyor_client.show_plan(plan_id).get('plan')
        #         stack_id = plan.get('stack_id')
        #                 # delete the stack
        #         self.orchestration_client.delete_stack(stack_id)

        self.conveyor_client.delete_plan(plan_id)
        self.clear_temp_servers(clone_servers)
        self.clear_temp_volumes(clone_volumes)

    @testtools.skip('Do not support clone between different az,need modify')
    @test.attr(type='smoke')
    def test_clone_update_fix_ip_in_diff_az(self):
        src_server = self.servers[0]
        init_servers = [_s['id'] for _s in self.servers]
        resources = [{"type": "OS::Nova::Server", "id": src_server['id']}]
        params = {"type": 'clone', "resources": resources}
        plan = self.conveyor_client.create_plan(**params)
        plan_id = plan.get('plan').get('plan_id')
        update_resource = [{'res_id': 'port_0',
                            'fixed_ips': [{'subnet_id': {'get_resource': 'subnet_0'},
                                           'ip_address': self.update_fix_ip}],
                            'type': 'OS::Neutron::Port'}]
        params_clone = {"destination": self.clone_availability_zone,
                        "update_resources": update_resource}
        self.conveyor_client.clone(plan_id, **params_clone)
        self.wait_for_plan_status(self.conveyor_client, plan_id, 'finished')
        time.sleep(60)
        params = {'ip': self.update_fix_ip}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(1, len(servers))

        params = {'name': src_server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        clone_servers = []
        dst_server = [s for s in servers if s['id'] not in init_servers][0]
        # self.clone_servers.append(dst_server)
        clone_servers.append(dst_server)

        body = self.servers_client.list_volume_attachments(
            dst_server['id'])['volumeAttachments']
        self.assertEqual(2, len(body))
        clone_volumes = []
        for b in body:
            clone_volme = {'id': b['volumeId']}
            # self.clone_volumes.append(clone_volme)
            clone_volumes.append(clone_volme)

        #         server_details = self.servers_client.show_server(dst_server['id'])['server']
        #
        #         resouces_fields = { "metadata" : self.meta}
        #             #"key_name" : self.origin_keypair}
        #             #"security_groups" : self.update_security_group, }
        #
        #         for name, expected_value in resouces_fields.iteritems():
        #             self.assertEqual(expected_value, server_details[name])

        plan = self.conveyor_client.show_plan(plan_id).get('plan')

        #         stack_id = plan.get('stack_id')
        #                 # delete the stack
        #         self.orchestration_client.delete_stack(stack_id)

        self.conveyor_client.delete_plan(plan_id)
        self.clear_temp_servers(clone_servers)
        self.clear_temp_volumes(clone_volumes)

    # @testtools.skip('Do not support clone between different az')
    @test.attr(type='smoke')
    def test_clone_update_others_in_diff_az(self):
        src_server = self.servers[0]
        init_servers = [_s['id'] for _s in self.servers]
        resources = [{"type": "OS::Nova::Server", "id": src_server['id']}]
        params = {"type": 'clone', "resources": resources}
        plan = self.conveyor_client.create_plan(**params)
        plan_id = plan.get('plan').get('plan_id')
        update_resource = [{'res_id': 'network_0',
                            'id': self.update_net,
                            'type': 'OS::Neutron::Net'},
                           {'res_id': 'subnet_0',
                            'id': self.update_subnet,
                            'type': 'OS::Neutron::Subnet'},
                           #                            {'res_id': 'keypair_0',
                           #                             'id': self.update_keypair,
                           #                             'type': 'OS::Nova::KeyPair'},
                           #                            {'res_id': 'security_group_0',
                           #                             'id': self.update_security_group,
                           #                             'type': 'OS::Neutron::SecurityGroup'},
                           ]
        params_clone = {"destination": self.clone_availability_zone,
                        "update_resources": update_resource}
        self.conveyor_client.clone(plan_id, **params_clone)
        self.wait_for_plan_status(self.conveyor_client, plan_id, 'finished')
        time.sleep(60)
        params = {'name': src_server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        clone_servers = []
        dst_server = [s for s in servers if s['id'] not in init_servers][0]
        # self.clone_servers.append(dst_server)
        clone_servers.append(dst_server)

        body = self.servers_client.list_volume_attachments(
            dst_server['id'])['volumeAttachments']
        self.assertEqual(2, len(body))
        clone_volumes = []
        for b in body:
            clone_volme = {'id': b['volumeId']}
            # self.clone_volumes.append(clone_volme)
            clone_volumes.append(clone_volme)

        #         server_details = self.servers_client.show_server(dst_server['id'])['server']
        #
        #         resouces_fields = { "metadata" : self.meta}
        #             #"key_name" : self.origin_keypair}
        #             #"security_groups" : self.update_security_group, }
        #
        #         for name, expected_value in resouces_fields.iteritems():
        #             self.assertEqual(expected_value, server_details[name])

        plan = self.conveyor_client.show_plan(plan_id).get('plan')

        #         stack_id = plan.get('stack_id')
        #                 # delete the stack
        #         self.orchestration_client.delete_stack(stack_id)

        self.conveyor_client.delete_plan(plan_id)
        self.clear_temp_servers(clone_servers)
        self.clear_temp_volumes(clone_volumes)

    def clear_temp_servers(self, servers):
        LOG.debug('Clearing servers: %s', ','.join(
            server['id'] for server in servers))
        for server in servers:
            try:
                self.servers_client.delete_server(server['id'])
            except lib_exc.NotFound:
                # Something else already cleaned up the server, nothing to be
                # worried about
                pass
            except Exception:
                LOG.exception('Deleting server %s failed' % server['id'])

        for server in servers:
            try:
                waiters.wait_for_server_termination(self.servers_client,
                                                    server['id'])
            except Exception:
                LOG.exception('Waiting for deletion of server %s failed'
                              % server['id'])

    def clear_temp_volumes(self, volumes):

        for volume in volumes:
            try:
                self.volumes_client.delete_volume(volume['id'])
            except Exception:
                pass
        for volume in volumes:
            try:
                self.volumes_client.wait_for_resource_deletion(volume['id'])
            except Exception:
                pass
