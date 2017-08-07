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
import uuid

from tempest.api.conveyor import base
from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest.lib import exceptions as lib_exc
from tempest import test

from oslo_log import log as logging

CONF = config.CONF
LOG = logging.getLogger(__name__)


class CloneV1TestJSON(base.BaseConveyorTest):
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
        super(CloneV1TestJSON, cls).setup_clients()
        cls.client = cls.conveyor_client

    @classmethod
    def resource_setup(cls):
        super(CloneV1TestJSON, cls).resource_setup()
        cls.volume_size = CONF.conveyor.volume_size
        cls.availability_zone_ref = CONF.conveyor.availability_zone
        cls.volume_type_ref = CONF.conveyor.volume_type
        cls.net_ref = CONF.conveyor.origin_net_ref
        cls.subnet_ref = CONF.conveyor.origin_subnet_ref
        cls.update_net_ref = CONF.conveyor.update_net_ref
        cls.update_subnet_ref = CONF.conveyor.update_subnet_ref
        cls.image_ref = CONF.conveyor.image_ref
        cls.flavor_ref = CONF.conveyor.flavor_ref
        cls.meta = {'hello': 'world'}
        cls.name = data_utils.rand_name('server')
        cls.password = data_utils.rand_password()
        cls.networks = [{'uuid': cls.net_ref}]

    @classmethod
    def resource_cleanup(cls):
        super(CloneV1TestJSON, cls).resource_cleanup()

    @test.attr(type='conveyor_smoke')
    def test_clone_server_private_aws(self):
        srv_name = uuid.uuid4()
        server_initial = self.create_server(
            networks=self.networks,
            wait_until='ACTIVE',
            name=srv_name,
            metadata=self.meta,
            adminPass=self.password,
            availability_zone=self.availability_zone_ref)
        server = self.servers_client.show_server(server_initial['id'])['server']
        self.addCleanup(self.clear_temp_servers, [server])

        kwargs = {'plan_type': 'clone',
                  'clone_obj': [{'obj_type': 'OS::Nova::Server',
                                 'obj_id': server['id']}],
                  'plan_name': 'test_clone_server_private_aws'}
        plan = self.conveyor_client.create_plan(**kwargs)['plan']
        self.addCleanup(self._clean_plans, [plan['plan_id']])

        cl_res = []
        cl_res.append({'id': server['id'], 'type': 'OS::Nova::Server'})
        cl_res.append({'id': self.flavor_ref, 'type': 'OS::Nova::Flavor'})
        cl_res.append({'id': self.net_ref, 'type': 'OS::Neutron::Net'})
        clone_kwargs = {
            'plan_id': plan['plan_id'],
            'availability_zone_map': {
                self.availability_zone_ref: CONF.conveyor.aws_region},
            'clone_resources': cl_res,
            'copy_data': False
        }
        self.conveyor_client.clone(**clone_kwargs)
        self.wait_for_plan_status(self.conveyor_client,
                                  plan['plan_id'],
                                  'plan_status',
                                  ['finished'])
        params = {'name': server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        self.client.delete_cloned_resource(plan['plan_id'])
        self.wait_for_plan_status(self.conveyor_client,
                                  plan['plan_id'],
                                  'task_status',
                                  ['finished'])

    def _clean_plan_resource(self, plan_ids):
        LOG.info('Clean create plan: %s', plan_ids)
        for plan_id in plan_ids:
            self.client.delete_cloned_resource(plan_id)
            self.wait_for_plan_status(self.conveyor_client,
                                      plan_id,
                                      ['finished'])

    def _clean_plans(self, plan_ids):
        LOG.info('Clean create plan: %s', plan_ids)
        for plan_id in plan_ids:
            self.client.delete_plan(plan_id)

    @test.attr(type='conveyor_smoke')
    def test_clone_server_aws_private(self):
        srv_name = uuid.uuid4()
        server_initial = self.create_server(
            networks=self.networks,
            wait_until='ACTIVE',
            name=srv_name,
            metadata=self.meta,
            adminPass=self.password,
            availability_zone=self.availability_zone_ref)
        server = self.servers_client.show_server(server_initial['id'])['server']
        self.addCleanup(self.clear_temp_servers, [server])

        kwargs = {'plan_type': 'clone',
                  'clone_obj': [{'obj_type': 'OS::Nova::Server',
                                 'obj_id': server['id']}],
                  'plan_name': 'test_clone_server_aws_private'}
        plan = self.conveyor_client.create_plan(**kwargs)['plan']
        self.addCleanup(self._clean_plans, [plan['plan_id']])

        cl_res = []
        cl_res.append({'id': server['id'], 'type': 'OS::Nova::Server'})
        cl_res.append({'id': self.flavor_ref, 'type': 'OS::Nova::Flavor'})
        cl_res.append({'id': self.net_ref, 'type': 'OS::Neutron::Net'})
        clone_kwargs = {
            'plan_id': plan['plan_id'],
            'availability_zone_map': {
                CONF.conveyor.aws_region: self.availability_zone_ref},
            'clone_resources': cl_res,
            'copy_data': False
        }
        self.conveyor_client.clone(**clone_kwargs)
        self.wait_for_plan_status(self.conveyor_client,
                                  plan['plan_id'],
                                  'plan_status',
                                  ['finished'])
        params = {'name': server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        self.client.delete_cloned_resource(plan['plan_id'])
        self.wait_for_plan_status(self.conveyor_client,
                                  plan['plan_id'],
                                  'task_status',
                                  ['finished'])

    @test.attr(type='conveyor_smoke')
    def test_clone_server_and_update_net(self):
        srv_name = uuid.uuid4()
        server_initial = self.create_server(
            networks=self.networks,
            wait_until='ACTIVE',
            name=srv_name,
            metadata=self.meta,
            adminPass=self.password,
            availability_zone=self.availability_zone_ref)
        server = self.servers_client.show_server(server_initial['id'])['server']
        self.addCleanup(self.clear_temp_servers, [server])

        kwargs = {'plan_type': 'clone',
                  'clone_obj': [{'obj_type': 'OS::Nova::Server',
                                 'obj_id': server['id']}],
                  'plan_name': 'test_clone_server_and_update_net'}
        plan = self.conveyor_client.create_plan(**kwargs)['plan']
        self.addCleanup(self._clean_plans, [plan['plan_id']])

        cl_res = []
        cl_res.append({'id': server['id'], 'type': 'OS::Nova::Server'})
        cl_res.append({'id': self.flavor_ref, 'type': 'OS::Nova::Flavor'})
        cl_res.append({'id': self.net_ref, 'type': 'OS::Neutron::Net'})
        update_res = []
        update_res.append({
            'enable_dhcp': True,
            'name': 'tempest-test-subnet-1',
            'resource_type': 'OS::Neutron::Subnet',
            'resource_id': self.subnet_ref
        })
        update_res.append({
            'shared': False,
            'name': 'tempest-test-net-1',
            'resource_type': 'OS::Neutron::Net',
            'resource_id': self.net_ref
        })
        kwargs = {
            'plan_id': plan['plan_id'],
            'availability_zone_map': {
                self.availability_zone_ref: CONF.conveyor.aws_region},
            'update_resources': update_res,
            'clone_resources': cl_res,
            'copy_data': False
        }
        self.conveyor_client.clone(**kwargs)
        self.wait_for_plan_status(self.conveyor_client,
                                  plan['plan_id'],
                                  'plan_status',
                                  ['finished'])
        params = {'name': server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        cloned_srvs = \
            [srv for srv in servers if srv['id'] != server_initial['id']][0]
        src_ips = self.servers_client.list_addresses(
            server_initial['id'])['addresses']
        des_ips = self.servers_client.list_addresses(
            cloned_srvs['id'])['addresses']
        for i_k, i_v in src_ips.items():
            d_k = des_ips.get('tempest-test-net-1', None)
            self.assertIsNotNone(d_k)
            self.assertEqual(len(i_v), len(d_k))
            self.assertEqual(i_v[0].get('addr'), d_k[0].get('addr'))
        self.client.delete_cloned_resource(plan['plan_id'])
        self.wait_for_plan_status(self.conveyor_client,
                                  plan['plan_id'],
                                  'task_status',
                                  ['finished'])

    @test.attr(type='conveyor_smoke')
    def test_clone_server_and_replace_net(self):
        srv_name = uuid.uuid4()
        server_initial = self.create_server(
            networks=self.networks,
            wait_until='ACTIVE',
            name=srv_name,
            metadata=self.meta,
            adminPass=self.password,
            availability_zone=self.availability_zone_ref)
        server = self.servers_client.show_server(server_initial['id'])['server']
        self.addCleanup(self.clear_temp_servers, [server])
        interfaces = self.interfaces_client.list_interfaces(
            server_initial['id'])['interfaceAttachments'][0]

        kwargs = {'plan_type': 'clone',
                  'clone_obj': [{'obj_type': 'OS::Nova::Server',
                                 'obj_id': server['id']}],
                  'plan_name': 'test_clone_server_and_replace_net'}
        plan = self.conveyor_client.create_plan(**kwargs)['plan']
        self.addCleanup(self._clean_plans, [plan['plan_id']])

        cl_res = []
        cl_res.append({'id': server['id'], 'type': 'OS::Nova::Server'})
        cl_res.append({'id': self.flavor_ref, 'type': 'OS::Nova::Flavor'})
        cl_res.append({'id': self.update_net_ref, 'type': 'OS::Neutron::Net'})
        cl_res.append({'id': self.update_subnet_ref,
                       'type': 'OS::Neutron::Subnet'})
        update_res = []
        update_res.append({
            'fixed_ips': [{
                'subnet_id': self.update_subnet_ref,
                'ip_address': ''
            }],
            'resource_type': 'OS::Neutron::Port',
            'resource_id': interfaces['port_id']
        })
        rep_res = []
        rep_res.append({
            'src_id': self.net_ref,
            'des_id': self.update_net_ref,
            'resource_type': 'OS::Neutron::Net'
        })
        rep_res.append({
            'src_id': self.subnet_ref,
            'des_id': self.update_subnet_ref,
            'resource_type': 'OS::Neutron::Subnet'
        })
        kwargs = {
            'plan_id': plan['plan_id'],
            'availability_zone_map': {
                self.availability_zone_ref: CONF.conveyor.aws_region},
            'update_resources': update_res,
            'clone_resources': cl_res,
            'replace_resources': rep_res,
            'copy_data': False
        }
        self.conveyor_client.clone(**kwargs)
        self.wait_for_plan_status(self.conveyor_client,
                                  plan['plan_id'],
                                  'plan_status',
                                  ['finished'])
        params = {'name': server['name']}
        body = self.servers_client.list_servers(**params)
        servers = body['servers']
        self.assertEqual(2, len(servers))
        self.client.delete_cloned_resource(plan['plan_id'])
        self.wait_for_plan_status(self.conveyor_client,
                                  plan['plan_id'],
                                  'task_status',
                                  ['finished'])

    @test.attr(type='conveyor_smoke')
    def test_clone_server_adding_volume_private_aws(self):
        pass

    @test.attr(type='conveyor_smoke')
    def test_clone_server_adding_volume_aws_private(self):
        pass

    @test.attr(type='conveyor_smoke')
    def test_clone_project_adding_server_private_aws(self):
        pass

    @test.attr(type='conveyor_smoke')
    def test_clone_project_adding_server_aws_private(self):
        pass

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
