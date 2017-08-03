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

        # cls.volume = cls.volumes_client.create_volume(
        #     size=cls.volume_size,
        #     display_name='volume_resource',
        #     availability_zone=cls.availability_zone_ref,
        #     volume_type=cls.volume_type_ref)['volume']
        # cls.volumes.append(cls.volume)
        # waiters.wait_for_volume_status(cls.volumes_client,
        #                                cls.volume['id'], 'available')

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
    def test_clone_server_private_aws(self):
        pass

    @test.attr(type='conveyor_smoke')
    def test_clone_server_aws_private(self):
        kwargs = {'plan_type': 'clone',
                  'clone_obj': [{'obj_type': 'OS::Cinder::Volume',
                                 'obj_id': self.volume['id']}],
                  'plan_name': 'test-create-plan'}

        plan = self.conveyor_client.create_plan(**kwargs)['plan']
        self.wait_for_plan_status(self.conveyor_client,
                                  plan['plan_id'],
                                  'available')

    @test.attr(type='conveyor_smoke')
    def test_clone_server_and_update_net(self):
        pass

    @test.attr(type='conveyor_smoke')
    def test_clone_server_and_replace_net(self):
        pass

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
