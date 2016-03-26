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
from tempest.common.utils import data_utils as utils
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


class ConveyorMigrateTest(base.BaseConveyorTest):
    """Test the conveyor clone.

    Tests for  clone template and export clone template
    """
    
    @classmethod
    def setup_clients(cls):
        super(ConveyorMigrateTest, cls).setup_clients()
    
    
        
    @classmethod
    def resource_setup(cls):
        super(ConveyorMigrateTest, cls).resource_setup()
        cls.origin_keypair = CONF.conveyor.origin_keypair_ref
        cls.update_keypair = CONF.conveyor.update_keypair_ref
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
        
        cls.password = data_utils.rand_password()
        networks = [{'uuid': cls.origin_net}]
        
#         cls.key_name = data_utils.rand_name('key') 
#         cls.keypairs_client.create_keypair(name=cls.key_name)
#         cls.origin_keypair = cls.key_name
#         cls.keypairs.append(cls.key_name)
  
    @classmethod
    def resource_cleanup(cls):
        super(ConveyorMigrateTest, cls).resource_cleanup()
    
      
    @test.attr(type='smoke')
    def test_migrate_in_same_az(self):
        name = data_utils.rand_name('server')
        src_server = self._create_migrate_vm(name)
        resources = [{"type": "OS::Nova::Server", "id": src_server['id']}]
        params =  {"type": 'migrate', "resources": resources}
        plan = self.conveyor_client.create_plan(**params)
        plan_id = plan.get('plan').get('plan_id')
        params_migrate = {"destination" :self.availability_zone}
        self.conveyor_client.migrate(plan_id, **params_migrate)
        self.wait_for_plan_status(self.conveyor_client, plan_id, 'finished')
        params = {'name': src_server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        #self.assertEqual(1, len(servers))
        dst_server =  servers[0]
        self.servers.append(dst_server)
        body = self.servers_client.list_volume_attachments(
            dst_server['id'])['volumeAttachments']
        for b in body:
            clone_volme ={'id':b['volumeId']}
            #self.clone_volumes.append(clone_volme)
            self.clone_volumes.append(clone_volme)
#         body = self.servers_client.list_volume_attachments(
#             dst_server['id'])['volumeAttachments']
#         self.assertEqual(2, len(body))
#         
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
    
    @test.attr(type='smoke')
    def test_migrate_in_diff_az(self):
        name = data_utils.rand_name('server')
        src_server =  self._create_migrate_vm(name)
        resources = [{"type": "OS::Nova::Server", "id": src_server['id']}]
        params =  {"type": 'migrate', "resources": resources}
        plan = self.conveyor_client.create_plan(**params)
        plan_id = plan.get('plan').get('plan_id')
        params_migrate = {"destination" :self.clone_availability_zone}
        self.conveyor_client.migrate(plan_id, **params_migrate)
        self.wait_for_plan_status(self.conveyor_client, plan_id, 'finished')
        params = {'name': src_server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        dst_server =  servers[0]
        self.servers.append(dst_server)
        
        body = self.servers_client.list_volume_attachments(
            dst_server['id'])['volumeAttachments']
        for b in body:
            clone_volme ={'id':b['volumeId']}
            #self.clone_volumes.append(clone_volme)
            self.clone_volumes.append(clone_volme)
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
        
    @classmethod
    def _create_migrate_vm(cls, name): 
       
        networks = [{'uuid': cls.origin_net}]
        server_initial = cls.create_server(
            name = name,
            image_id=cls.image,
            flavor=cls.flavor,
            networks=networks,
            wait_until='ACTIVE',
            metadata=cls.meta, 
            adminPass=cls.password,
            #key_name = cls.key_name,
            availability_zone = cls.availability_zone )
        server = (cls.servers_client.show_server(server_initial['id'])
                      ['server'])
        
        #cls.servers_client.add_security_group(server_initial['id'], name=cls.origin_security_group)
        #cls.servers.append(server)
        volume_01 = cls.volumes_client.create_volume(
            size=CONF.conveyor.volume_size, display_name='test01', 
            availability_zone= cls.availability_zone,
            volume_type = CONF.conveyor.volume_type)['volume'] 
        waiters.wait_for_volume_status(cls.volumes_client,
                                   volume_01['id'], 'available')
        #cls.volumes.append(volume_01)
        
        
        cls.volumes.append(volume_01)
        volume_02 = cls.volumes_client.create_volume(
            size=CONF.conveyor.volume_size, display_name='test02',
            availability_zone= cls.availability_zone,
            volume_type = CONF.conveyor.volume_type)['volume']
        waiters.wait_for_volume_status(cls.volumes_client,
                                   volume_02['id'], 'available')

        #cls.volumes.append(volume_02)
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
        return server
