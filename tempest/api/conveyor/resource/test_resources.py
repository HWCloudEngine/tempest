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
import operator
from tempest.api.conveyor import base
from tempest import test
from tempest import config
from tempest.common.utils import data_utils
from tempest.common import waiters

from oslo_log import log as logging
CONF = config.CONF
LOG = logging.getLogger(__name__)

class ResourcesV1TestJSON(base.BaseConveyorTest):

        
    def assertResourceIn(self, fetched_res, res_list, fields=None):
        
        if not fields:
            self.assertIn(fetched_res, res_list)
            
        res_list = map(operator.itemgetter(*fields), res_list)
        fetched_res = map(operator.itemgetter(*fields), [fetched_res])[0]
        
        self.assertIn(fetched_res, res_list)
        
    def assertListIn(self, expected_list, fetched_list):
        missing_items = [v for v in expected_list if v not in fetched_list]
        if len(missing_items) == 0:
            return
        raw_msg = "%s not in fetched_list %s" \
                                  % (missing_items, fetched_list)
        self.fail(raw_msg)

    @classmethod
    def setup_clients(cls):
        super(ResourcesV1TestJSON, cls).setup_clients()
        cls.client = cls.conveyor_client
        
    @classmethod
    def resource_setup(cls):
        super(ResourcesV1TestJSON, cls).resource_setup()
              
        #cls.keypair_ref = CONF.conveyor.origin_keypair_ref
        cls.secgroup_ref = CONF.conveyor.origin_security_group_ref
        cls.net_ref = CONF.conveyor.origin_net_ref
        #cls.public_net_ref = CONF.conveyor.public_net_ref
        cls.floating_ip_pool_ref = CONF.conveyor.floating_ip_pool_ref
        #cls.subnet_ref = CONF.conveyor.origin_subnet_ref
        cls.image_ref = CONF.conveyor.image_ref
        cls.flavor_ref = CONF.conveyor.flavor_ref
        cls.availability_zone_ref = CONF.conveyor.availability_zone
        
        cls.volume_size = CONF.conveyor.volume_size
        cls.volume_type_ref = CONF.conveyor.volume_type
        
        cls.meta = {'hello': 'world'}
        cls.name = data_utils.rand_name('server')
        cls.password = data_utils.rand_password()
        networks = [{'uuid': cls.net_ref}]
        
         
#         key_name = data_utils.rand_name('key')
#         cls.keypair = cls.keypairs_client.create_keypair(name=key_name)['keypair']
        
        server_initial = cls.create_server(
            networks=networks,
            wait_until='ACTIVE',
            #name=cls.name,
            name="server_resource",
            metadata=cls.meta,
            adminPass=cls.password,
            #key_name=key_name,
            #security_groups=cls.secgroup_ref,
            availability_zone=cls.availability_zone_ref)

        cls.server = (cls.servers_client.show_server(server_initial['id'])['server'])
        cls.servers.append(cls.server)
        
        cls.volume = cls.volumes_client.create_volume(
            size=cls.volume_size, 
            #display_name='volume01',
            display_name='volume_resource',
            availability_zone=cls.availability_zone_ref,
            volume_type=cls.volume_type_ref)['volume']
            
        cls.volumes.append(cls.volume)
        waiters.wait_for_volume_status(cls.volumes_client,
                                   cls.volume['id'], 'available')
        
        #Attach the volume to the server
        cls.servers_client.attach_volume(
           server_initial['id'],
           volumeId=cls.volume['id'])['volumeAttachment']
        waiters.wait_for_volume_status(cls.volumes_client,
                                   cls.volume['id'], 'in-use')
        #Allocate floating ip to the server
        #body = cls.floating_ips_client.create_floating_ip( \
        #                                        pool=cls.floating_ip_pool_ref)['floating_ip']
        
        #cls.floating_ip_id = body['id']
        #cls.floating_ip = body['ip']
        
        #cls.floating_ips_client.associate_floating_ip_to_server(cls.floating_ip,
        #                                                        server_initial['id'])
#         #Add security group    
#         sec_name = data_utils.rand_name(cls.__name__ + "-secgroup")
#         cls.sec_group = cls.security_groups_client.create_security_group(
#             name=sec_name, description="")['security_group']
#         cls.servers_client.add_security_group(server_initial['id'], name=cls.sec_group['name'])    
            
        cls.server = (cls.servers_client.show_server(server_initial['id'])['server'])
        #cls.servers.append(cls.server) 
        
            
    @classmethod
    def resource_cleanup(cls):
        
        #if cls.floating_ip_id:
        #    cls.floating_ips_client.delete_floating_ip(cls.floating_ip_id)
        #if cls.sec_group:
        #    cls.security_groups_client.delete_security_group(cls.sec_group['id'])
#         if cls.keypair:
#             cls.keypairs_client.delete_keypair(cls.keypair['name'])
        super(ResourcesV1TestJSON, cls).resource_cleanup() 
        
    
    @test.attr(type='smoke')
    @test.idempotent_id('ee9aa589-d6f0-4365-aa66-613efd3c117f')
    def test_list_types(self):
        res_types = self.client.show_resource_types()['types']
        
        instance_type = {'type': 'OS::Nova::Server'}
        volume_type = {'type': 'OS::Cinder::Volume'}
        
        self.assertIn(instance_type, res_types)
        self.assertIn(volume_type, res_types)


    @test.attr(type='smoke')
    @test.idempotent_id('034e065b-8822-4017-9586-349ca735d06a')
    def test_list_resources(self):
        res = self.client.list_resources({'type': 'OS::Nova::Server', 
                                          'all_tenants': 1})['resources']
        self.assertResourceIn(self.server, res, fields=['id'])
        

    @test.attr(type='smoke')
    @test.idempotent_id('186a8645-3a40-432b-8b78-e82e5e27aa49')
    def test_show_resource(self):
        res = self.client.show_resource(self.server['id'], 
                                        type='OS::Nova::Server')['resource']
        #fields = ['id', 'name', 'flavor', 'key_name', 
        #          'image', 'os-extended-volumes:volumes_attached']
        fields = ['id', 'name']
        self.assertResourceIn(self.server, [res], fields=fields)
        self.assertListIn(self.server['security_groups'], res['security_groups'])
        for net, detail in self.server['addresses'].items():
            self.assertIn(net, res['addresses'].keys())
            self.assertEqual(detail, res['addresses'][net])

    @test.attr(type='smoke')
    @test.idempotent_id('186a8645-3a40-432b-8b78-e82e5e27aa49')
    def test_create_show_update_delete(self):
        #Test create a plan by specified resource
        kwargs = {'type': 'clone', 'resources': 
                  [{'type': 'OS::Nova::Server', 'id': self.server['id']}]}
        test_plan = self.client.create_plan(**kwargs)['plan']

#         expected_plan_resources = ['server_0', 'flavor_0', 'keypair_0', 
#                                    'volume_0', 'volume_type_0', 'network_0', 
#                                    'subnet_0', 'port_0', 'router_0', 'floatingip_0', 
#                                    'security_group_0', 'router_0_interface_0'
#                                    ]
        
        expected_plan_resources = ['server_0', 'flavor_0', 
                                   'volume_0', 'network_0', 
                                   'subnet_0', 'port_0', 'security_group_0',
                                   ]
        self.assertListIn(expected_plan_resources, 
                          test_plan['original_dependencies'].keys())
        
        #Test show a plan
        plan = self.client.show_plan(test_plan['plan_id'])['plan']
        
        self.assertEqual(plan['plan_status'], 'initiating')
        self.assertEqual(plan['plan_type'], 'clone')
        
        self.assertListIn(expected_plan_resources, 
                          plan['original_resources'])
        
        res = plan['original_resources']
        self.assertEqual(res['server_0']['id'], self.server['id'])
        self.assertEqual(res['server_0']['properties']['availability_zone'],
                         self.availability_zone_ref)
        
        self.assertEqual(res['volume_0']['id'], self.volume['id'])
        self.assertEqual(res['flavor_0']['id'], self.server['flavor']['id'])
        #self.assertEqual(res['keypair_0']['id'], self.keypair['name'])
        self.assertEqual(res['network_0']['id'], self.net_ref)
        
        server_addrs = []
        for detail in self.server['addresses'].values():
            for ip in detail:
                server_addrs.append(ip['addr'])
        
        res_addrs = []
        for ip in res['port_0']['properties']['fixed_ips']:
            res_addrs.append(ip['ip_address'])
        self.assertListIn(res_addrs, server_addrs)
        
        server_groups = [group['name'] for group in self.server['security_groups']]
        res_group = res['security_group_0']['properties']['name']
        if res_group == "_default":
            res_group = "default"
        self.assertIn(res_group, server_groups)
       
 	"""
        #Update plan
        update_keypair_name = data_utils.rand_name('key')
        self.keypairs_client.create_keypair(name=update_keypair_name)
        self.addCleanup(self.keypairs_client.delete_keypair, update_keypair_name)
        
        update_resources = [{'res_id': 'keypair_0',
                            'id': update_keypair_name,
                            'type': 'OS::Nova::KeyPair'}]
        
        self.conveyor_client.export_clone_template(test_plan['plan_id'], 
                                   update_resources=update_resources)
        self.wait_for_plan_status(self.client, test_plan['plan_id'], 'available')
         
        #Show plan
        plan = self.client.show_plan(test_plan['plan_id'])['plan']
        self.assertEqual(plan['updated_resources']['keypair_0']['id'], 
                                                    update_keypair_name)
        """
        #Show all plans
        plans = self.client.list_plans(detail=True)['plans']
        self.assertResourceIn(test_plan, plans, fields=['plan_id'])
        
        #Show server_0 in plan
        server_0_res = self.client.show_resource_of_plan('server_0', 
                                    plan_id=test_plan['plan_id'])['resource']
                                        
        self.assertEqual(server_0_res['id'], self.server['id'])                                
        self.assertEqual(server_0_res['properties']['name'], self.server['name'])
        
        #Delete plan
        self.client.delete_plan(test_plan['plan_id'])
        self.wait_for_server_deletion(self.client, test_plan['plan_id'])


    @test.attr(type='smoke')
    @test.idempotent_id('ee3eb3d9-8b64-43e2-a058-355bc8c501b4')
    def test_create_plan_by_template(self):
        template = self.read_template('clone_template')
        template_dict = self.load_template('clone_template')
        plan = self.client.create_plan_by_template(template)['plan']
        self.wait_for_plan_status(self.client, plan['plan_id'], 'available')
        plan = self.client.show_plan(plan['plan_id'])['plan']
        self._verify_plan_by_template(template_dict, plan)
    
    
    @test.attr(type='smoke')
    @test.idempotent_id('a4dbc21f-5709-4aec-93be-48ee4f2ed886')
    def test_create_plan_by_expired_template(self):
        template = self.read_template('expired_template')
        try:
            self.client.create_plan_by_template(template)['plan']
        except Exception:
            return
        msg = "Test failed: using the expired template to create a plan succeed!"
        self.fail(msg)
            
          
    def _verify_plan_by_template(self, template, plan):
        #self.assertEqual(plan['plan_status'], 'available')
        self.assertEqual(plan['plan_type'], template['plan_type'])
        
        fields = ['type', 'properties']
        for res_name, res in template['resources'].items():
            self.assertListIn([res_name], plan['original_resources'].keys())
            self.assertListIn([res_name], plan['original_dependencies'].keys())
            self.assertResourceIn(res, 
                                  plan['original_resources'].values(), 
                                  fields=fields)
            
