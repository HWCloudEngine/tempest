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
        cls.image_ref = CONF.conveyor.image_ref
        cls.flavor_ref = CONF.conveyor.flavor_ref
        cls.meta = {'hello': 'world'}
        cls.name = data_utils.rand_name('server')
        cls.password = data_utils.rand_password()
        networks = [{'uuid': cls.net_ref}]

        cls.volume = cls.volumes_client.create_volume(
            size=cls.volume_size,
            display_name='volume_resource',
            availability_zone=cls.availability_zone_ref,
            volume_type=cls.volume_type_ref)['volume']
        cls.volumes.append(cls.volume)
        waiters.wait_for_volume_status(cls.volumes_client,
                                       cls.volume['id'], 'available')

        server_initial = cls.create_server(
            networks=networks,
            wait_until='ACTIVE',
            name="server_resource",
            metadata=cls.meta,
            adminPass=cls.password,
            availability_zone=cls.availability_zone_ref)
        cls.server = (
            cls.servers_client.show_server(server_initial['id'])['server'])
        cls.servers.append(cls.server)

        kwargs = {'plan_type': 'clone',
                  'clone_obj': [{'obj_type': 'OS::Cinder::Volume',
                                 'obj_id': cls.volume['id']}],
                  'plan_name': 'test-create-plan'}
        cls.conveyor_plan = cls.conveyor_client.create_plan(**kwargs)['plan']
        cls.wait_for_plan_status(cls.conveyor_client,
                                 cls.conveyor_plan['plan_id'],
                                 'available')

    @classmethod
    def resource_cleanup(cls):
        super(CloneV1TestJSON, cls).resource_cleanup()

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('d17bda3c-b39e-4d5c-91d3-8ae8becf0d9f')
    def test_clone_with_server(self):
        pass

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('60cc6797-43a9-4275-8549-5ba853a48800')
    def test_clone_with_server_and_copy_data(self):
        pass

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('7b44c124-073b-4917-9816-be754bfb5cbc')
    def test_clone_with_server_and_update_net(self):
        pass

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('9b2b4557-aa05-4db3-a56c-39caea865cb2')
    def test_clone_with_server_and_update_security(self):
        pass

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('4bbb3dd1-144c-40de-8c91-f5f2c59821b8')
    def test_clone_with_server_and_update_port(self):
        pass

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('ce2fd46f-1a6e-4b16-a749-d64c820a04ae')
    def test_clone_with_server_and_update_userdata(self):
        pass

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('8a452d3a-06e5-4448-a51b-15ff330a77e8')
    def test_clone_with_server_and_replace_net(self):
        pass

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('e44d5a36-b349-4380-974a-725f764f63fd')
    def test_adding_clone_by_adding_server(self):
        pass

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('04b7bf12-5de0-46b5-af8d-22104833c256')
    def test_adding_clone_by_adding_volume(self):
        pass

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('141057cf-5b8c-44e1-b4d6-07bf0f76af47')
    def test_adding_clone_by_adding_port(self):
        pass
