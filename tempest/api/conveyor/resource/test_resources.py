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
from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest import test

from oslo_log import log as logging
CONF = config.CONF
LOG = logging.getLogger(__name__)


class ConveyorResourceV1TestJSON(base.BaseConveyorTest):

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
        super(ConveyorResourceV1TestJSON, cls).setup_clients()
        cls.client = cls.conveyor_client

    @classmethod
    def resource_setup(cls):
        super(ConveyorResourceV1TestJSON, cls).resource_setup()
        cls.net_ref = CONF.conveyor.origin_net_ref
        cls.image_ref = CONF.conveyor.image_ref
        cls.flavor_ref = CONF.conveyor.flavor_ref
        cls.availability_zone_ref = CONF.conveyor.availability_zone
        cls.volume_size = CONF.conveyor.volume_size
        cls.volume_type_ref = CONF.conveyor.volume_type
        cls.name = data_utils.rand_name('server')
        cls.password = data_utils.rand_password()
        networks = [{'uuid': cls.net_ref}]
        server_initial = cls.create_server(
            networks=networks,
            wait_until='ACTIVE',
            name="server_resource",
            adminPass=cls.password,
            availability_zone=cls.availability_zone_ref,
            image_id=cls.image_ref,
            flavor=cls.flavor_ref)

        cls.server = \
            (cls.servers_client.show_server(server_initial['id'])['server'])
        cls.servers.append(cls.server)

        cls.volume = cls.volumes_client.create_volume(
            size=cls.volume_size,
            display_name='volume_resource',
            availability_zone=cls.availability_zone_ref,
            volume_type=cls.volume_type_ref)['volume']

        cls.volumes.append(cls.volume)
        waiters.wait_for_volume_status(cls.volumes_client,
                                       cls.volume['id'], 'available')

        cls.servers_client.attach_volume(
            server_initial['id'],
            volumeId=cls.volume['id'])['volumeAttachment']
        waiters.wait_for_volume_status(cls.volumes_client,
                                       cls.volume['id'], 'in-use')

        cls.server = \
            (cls.servers_client.show_server(server_initial['id'])['server'])

    @classmethod
    def resource_cleanup(cls):

        super(ConveyorResourceV1TestJSON, cls).resource_cleanup()

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('ee9aa589-d6f0-4365-aa66-613efd3c117f')
    def test_list_types(self):
        res_types = self.client.show_resource_types()['types']

        instance_type = {'type': 'OS::Nova::Server'}
        volume_type = {'type': 'OS::Cinder::Volume'}

        self.assertIn(instance_type, res_types)
        self.assertIn(volume_type, res_types)

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('034e065b-8822-4017-9586-349ca735d06a')
    def test_list_resources(self):
        res = self.client.list_resources({'type': 'OS::Nova::Server',
                                          'all_tenants': 1})['resources']
        self.assertResourceIn(self.server, res, fields=['id'])

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('186a8645-3a40-432b-8b78-e82e5e27aa49')
    def test_show_resource(self):
        res = self.client.show_resource(self.server['id'],
                                        type='OS::Nova::Server')['resource']

        fields = ['id', 'name']

        self.assertResourceIn(self.server, [res], fields=fields)

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('a4dbc21f-5709-4aec-93be-48ee4f2ed887')
    def test_list_clone_resources_attribute(self):
        kwargs = dict(plan_type='clone',
                      plan_name='test',
                      clone_obj=[{'obj_id': self.server['id'],
                                  'obj_type': 'OS::Nova::Server'}])
        plan = self.client.create_plan(**kwargs)
        plan_id = plan.get('plan', {}).get('plan_id', '')
        plan_ids = []
        plan_ids.append(plan_id)
        self.addCleanup(self._clean_plans, plan_ids)
        az_list = \
            self.client.list_clone_resources_attribute(plan_id,
                                                       'availability_zone')
        az = az_list['attribute_list'][0]
        self.assertEqual(self.availability_zone_ref, az)

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('a4dbc21f-5709-4aec-93be-48ee4f2ed886')
    def test_build_resources_topo(self):
        kwargs = dict(plan_type='clone',
                      plan_name='test',
                      clone_obj=[{'obj_id': self.server['id'],
                                  'obj_type': 'OS::Nova::Server'}])
        plan = self.client.create_plan(**kwargs)
        plan_id = plan.get('plan', {}).get('plan_id', '')
        plan_ids = []
        plan_ids.append(plan_id)
        self.addCleanup(self._clean_plans, plan_ids)
        src_az = self.availability_zone_ref
        az_map = {}
        az_map[src_az] = src_az
        topo = \
            self.client.build_resources_topo(plan_id,
                                             az_map)
        self.assertEqual(plan_id, topo['plan_id'])

    def _clean_plans(self, plan_ids):
        LOG.info('Clean create plan: %s', plan_ids)
        for plan_id in plan_ids:
            self.client.delete_plan(plan_id)
