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
from tempest.common import waiters
from tempest import config
from tempest import test

from oslo_log import log as logging

CONF = config.CONF
LOG = logging.getLogger(__name__)


class PlanV1TestJSON(base.BaseConveyorTest):
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
        super(PlanV1TestJSON, cls).setup_clients()
        cls.client = cls.conveyor_client

    @classmethod
    def resource_setup(cls):
        super(PlanV1TestJSON, cls).resource_setup()
        cls.volume_size = CONF.conveyor.volume_size
        cls.availability_zone_ref = CONF.conveyor.availability_zone
        cls.volume_type_ref = CONF.conveyor.volume_type
        cls.volume = cls.volumes_client.create_volume(
            size=cls.volume_size,
            display_name='volume_resource',
            availability_zone=cls.availability_zone_ref,
            volume_type=cls.volume_type_ref)['volume']
        cls.volumes.append(cls.volume)
        waiters.wait_for_volume_status(cls.volumes_client,
                                       cls.volume['id'], 'available')

        kwargs = {'plan_type': 'clone',
                  'clone_obj': [{'obj_type': 'OS::Cinder::Volume',
                                 'obj_id': cls.volume['id']}],
                  'plan_name': 'test-create-plan'}
        conveyor_plan = cls.conveyor_client.create_plan(**kwargs)['plan']
        cls.wait_for_plan_status(cls.conveyor_client,
                                 conveyor_plan['plan_id'],
                                 'available')
        cls.plan = (cls.conveyor_client.show_plan(
            conveyor_plan['plan_id'])['plan'])
        cls.plans.append(cls.plan)

    @classmethod
    def resource_cleanup(cls):
        super(PlanV1TestJSON, cls).resource_cleanup()

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('d7f09396-2d66-4b43-a9d1-6843170a86d2')
    def test_create_plan(self):
        self.assertEqual('available', self.plan['plan_status'])

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('773f8145-8cb8-4845-9c4d-e95c37b62a7b')
    def test_list_plan(self):
        res_plan = self.conveyor_client.list_plans(detail=True)
        self.assertEqual(1, len(res_plan['plans']))
        self.assertEqual(self.plan['plan_id'],
                         res_plan['plans'][0]['plan_id'])

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('45db29a4-d5e0-499d-ae18-45541184f62a')
    def test_show_plan(self):
        res_plan = self.conveyor_client.show_plan(
            self.plan['plan_id'])['plan']
        self.assertEqual(self.plan['plan_id'],
                         res_plan['plan_id'])
        self.assertEqual('test-create-plan', res_plan['plan_name'])
        self.assertEqual('available', res_plan['plan_status'])

    @test.attr(type='conveyor_smoke')
    @test.idempotent_id('0484faad-cdf8-4643-a56a-7f3b5eed40a8')
    def test_delete_plan(self):
        kwargs = {'plan_type': 'clone',
                  'clone_obj': [{'obj_type': 'OS::Cinder::Volume',
                                 'obj_id': self.volume['id']}],
                  'plan_name': 'test-delete-plan'}
        res_plan = self.conveyor_client.create_plan(**kwargs)['plan']
        self.wait_for_plan_status(self.conveyor_client, res_plan['plan_id'],
                                  'available')
        self.conveyor_client.delete_plan(res_plan['plan_id'])
        self.wait_for_plan_deletion(self.conveyor_client, res_plan['plan_id'])
