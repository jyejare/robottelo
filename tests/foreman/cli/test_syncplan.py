# -*- encoding: utf-8 -*-
"""Test class for Sync Plan CLI

@Requirement: Syncplan

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: CLI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from datetime import datetime, timedelta
from fauxfactory import gen_string
from random import randint
from robottelo import manifests
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    CLIFactoryError,
    make_org,
    make_product,
    make_repository,
    make_sync_plan,
)
from robottelo.cli.product import Product
from robottelo.cli.repository import Repository
from robottelo.cli.repository_set import RepositorySet
from robottelo.cli.subscription import Subscription
from robottelo.cli.syncplan import SyncPlan
from robottelo.constants import PRDS, REPOS, REPOSET
from robottelo.datafactory import (
    filtered_datapoint,
    valid_data_list,
    invalid_values_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    tier1,
    tier3,
    tier4,
    upgrade
)
from robottelo.ssh import upload_file
from robottelo.test import CLITestCase
from time import sleep


@filtered_datapoint
def valid_name_interval_create_tests():
    """Returns a list of valid data for interval create tests."""
    return [
        {u'name': gen_string('alpha', 15), u'interval': u'hourly'},
        {u'name': gen_string('alphanumeric', 15), u'interval': u'hourly'},
        {u'name': gen_string('numeric', 15), u'interval': u'hourly'},
        {u'name': gen_string('latin1', 15), u'interval': u'hourly'},
        {u'name': gen_string('utf8', 15), u'interval': u'hourly'},
        {u'name': gen_string('html', 15), u'interval': u'hourly'},
        {u'name': gen_string('alpha', 15), u'interval': u'daily'},
        {u'name': gen_string('alphanumeric', 15), u'interval': u'daily'},
        {u'name': gen_string('numeric', 15), u'interval': u'daily'},
        {u'name': gen_string('latin1', 15), u'interval': u'daily'},
        {u'name': gen_string('utf8', 15), u'interval': u'daily'},
        {u'name': gen_string('html', 15), u'interval': u'daily'},
        {u'name': gen_string('alpha', 15), u'interval': u'weekly'},
        {u'name': gen_string('alphanumeric', 15), u'interval': u'weekly'},
        {u'name': gen_string('numeric', 15), u'interval': 'weekly'},
        {u'name': gen_string('latin1', 15), u'interval': u'weekly'},
        {u'name': gen_string('utf8', 15), u'interval': u'weekly'},
        {u'name': gen_string('html', 15), u'interval': u'weekly'},
    ]


@filtered_datapoint
def valid_name_interval_update_tests():
    """Returns a list of valid data for interval update tests."""
    return[
        {u'name': gen_string('alpha', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('alphanumeric', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('numeric', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('latin1', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('utf8', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('html', 15),
         u'interval': u'daily', u'new-interval': u'hourly'},
        {u'name': gen_string('alpha', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('alphanumeric', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('numeric', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('latin1', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('utf8', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('html', 15),
         u'interval': u'weekly', u'new-interval': u'daily'},
        {u'name': gen_string('alpha', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('alphanumeric', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('numeric', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('latin1', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('utf8', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
        {u'name': gen_string('html', 15),
         u'interval': u'hourly', u'new-interval': u'weekly'},
    ]


class SyncPlanTestCase(CLITestCase):
    """Sync Plan CLI tests."""

    org = None

    # pylint: disable=unexpected-keyword-arg
    def setUp(self):
        """Tests for Sync Plans via Hammer CLI"""

        super(SyncPlanTestCase, self).setUp()

        if SyncPlanTestCase.org is None:
            SyncPlanTestCase.org = make_org(cached=True)

    def _make_sync_plan(self, options=None):
        """Make a sync plan and asserts its success"""

        if options is None:
            options = {}

        if not options.get('organization-id', None):
            options[u'organization-id'] = self.org['id']

        return make_sync_plan(options)

    def validate_repo_content(
            self, repo, content_types, after_sync=True, max_attempts=10):
        """Check whether corresponding content is present in repository before
        or after synchronization is performed

        :param repo: Repository instance to be validated
        :param content_types: List of repository content entities that should
            be validated (e.g. package, erratum, puppet_module)
        :param bool after_sync: Specify whether you perform validation before
            synchronization procedure is happened or after
        :param int max_attempts: Specify how many times to check for content
            presence. Delay between each attempt is 10 seconds. Default is 10
            attempts.

        """
        for _ in range(max_attempts):
            try:
                repo = Repository.info({'id': repo['id']})
                for content in content_types:
                    if after_sync:
                        self.assertGreater(
                            int(repo['content-counts'][content]), 0)
                    else:
                        self.assertFalse(int(repo['content-counts'][content]))
                break
            except AssertionError:
                sleep(30)
        else:
            repo = Repository.info({'id': repo['id']})
            self.assertNotEqual(
                repo['sync']['status'],
                'Not Synced',
                'Repository contains invalid number of content entities'
            )

    @tier1
    def test_positive_create_with_name(self):
        """Check if syncplan can be created with random names

        @id: dc0a86f7-4219-427e-92fd-29352dbdbfce

        @expectedresults: Sync plan is created and has random name
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_sync_plan = self._make_sync_plan({u'name': name})
                self.assertEqual(new_sync_plan['name'], name)

    @tier1
    def test_positive_create_with_description(self):
        """Check if syncplan can be created with random description

        @id: a1bbe81b-60f5-4a19-b400-a02a23fa1dfa

        @expectedresults: Sync plan is created and has random description
        """
        for desc in valid_data_list():
            with self.subTest(desc):
                new_sync_plan = self._make_sync_plan({u'description': desc})
                self.assertEqual(new_sync_plan['description'], desc)

    @tier1
    def test_positive_create_with_interval(self):
        """Check if syncplan can be created with varied intervals

        @id: 32eb0c1d-0c9a-4fb5-a185-68d0d705fbce

        @expectedresults: Sync plan is created and has selected interval
        """
        for test_data in valid_name_interval_create_tests():
            with self.subTest(test_data):
                new_sync_plan = self._make_sync_plan({
                    u'interval': test_data['interval'],
                    u'name': test_data['name'],
                })
                self.assertEqual(new_sync_plan['name'], test_data['name'])
                self.assertEqual(
                    new_sync_plan['interval'],
                    test_data['interval']
                )

    @tier1
    def test_negative_create_with_name(self):
        """Check if syncplan can be created with random names

        @id: 4c1aee35-271e-4ed8-9369-d2abfea8cfd9

        @expectedresults: Sync plan is created and has random name
        """
        for name in invalid_values_list():
            with self.subTest(name):
                with self.assertRaises(CLIFactoryError):
                    self._make_sync_plan({u'name': name})

    @tier1
    def test_positive_update_description(self):
        """Check if syncplan description can be updated

        @id: 00a279cd-1f49-4ebb-a59a-6f0b4e4cb83c

        @expectedresults: Sync plan is created and description is updated
        """
        new_sync_plan = self._make_sync_plan()
        for new_desc in valid_data_list():
            with self.subTest(new_desc):
                SyncPlan.update({
                    u'description': new_desc,
                    u'id': new_sync_plan['id'],
                })
                result = SyncPlan.info({u'id': new_sync_plan['id']})
                self.assertEqual(result['description'], new_desc)

    @tier1
    def test_positive_update_interval(self):
        """Check if syncplan interval be updated

        @id: d676d7f3-9f7c-4375-bb8b-277d71af94b4

        @expectedresults: Sync plan interval is updated
        """
        for test_data in valid_name_interval_update_tests():
            with self.subTest(test_data):
                new_sync_plan = self._make_sync_plan({
                    u'interval': test_data['interval'],
                    u'name': test_data['name'],
                })
                SyncPlan.update({
                    u'id': new_sync_plan['id'],
                    u'interval': test_data['new-interval'],
                })
                result = SyncPlan.info({u'id': new_sync_plan['id']})
                self.assertEqual(result['interval'], test_data['new-interval'])

    @skip_if_bug_open('bugzilla', 1336790)
    @tier1
    @upgrade
    def test_positive_update_sync_date(self):
        """Check if syncplan sync date can be updated

        @id: f0c17d7d-3e86-4b64-9747-6cba6809815e

        @expectedresults: Sync plan is created and sync plan is updated
        """
        # Set the sync date to today/right now
        today = datetime.now()
        sync_plan_name = gen_string('alphanumeric')
        new_sync_plan = self._make_sync_plan({
            u'name': sync_plan_name,
            u'sync-date': today.strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Assert that sync date matches data passed
        self.assertEqual(
            new_sync_plan['start-date'],
            today.strftime("%Y/%m/%d %H:%M:%S"),
        )
        # Set sync date 5 days in the future
        future_date = today + timedelta(days=5)
        # Update sync interval
        SyncPlan.update({
            u'id': new_sync_plan['id'],
            u'sync-date': future_date.strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Fetch it
        result = SyncPlan.info({
            u'id': new_sync_plan['id'],
        })
        self.assertNotEqual(result['start-date'], new_sync_plan['start-date'])
        self.assertGreater(
            datetime.strptime(
                result['start-date'],
                '%Y/%m/%d %H:%M:%S',
            ),
            datetime.strptime(
                new_sync_plan['start-date'],
                '%Y/%m/%d %H:%M:%S',
            ),
            'Sync date was not updated',
        )

    @tier1
    @upgrade
    def test_positive_delete_by_id(self):
        """Check if syncplan can be created and deleted

        @id: b5d97c6b-aead-422b-8d9f-4a192bbe4a3b

        @expectedresults: Sync plan is created and then deleted
        """
        for name in valid_data_list():
            with self.subTest(name):
                new_sync_plan = self._make_sync_plan({u'name': name})
                SyncPlan.delete({u'id': new_sync_plan['id']})
                with self.assertRaises(CLIReturnCodeError):
                    SyncPlan.info({'id': new_sync_plan['id']})

    @tier1
    def test_positive_info_enabled_field_is_displayed(self):
        """Check if Enabled field is displayed in sync-plan info output

        @id: 54e3a4ea-315c-4026-8101-c4605ca6b874

        @expectedresults: Sync plan Enabled state is displayed
        """
        new_sync_plan = self._make_sync_plan()
        result = SyncPlan.info({'id': new_sync_plan['id']})
        self.assertIsNotNone(result.get('enabled'))

    @tier4
    @upgrade
    def test_negative_synchronize_custom_product_past_sync_date(self):
        """Verify product won't get synced immediately after adding association
        with a sync plan which has already been started

        @id: c80f5c0c-3863-47da-8d7b-7d65c73664b0

        @expectedresults: Repository was not synchronized

        @BZ: 1279539

        @CaseLevel: System
        """
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'organization-id': self.org['id'],
            'sync-date': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        with self.assertRaises(AssertionError):
            self.validate_repo_content(
                repo,
                ['errata', 'package-groups', 'packages'],
                max_attempts=5,
            )

    @tier4
    @upgrade
    def test_positive_synchronize_custom_product_past_sync_date(self):
        """Create a sync plan with a past datetime as a sync date, add a
        custom product and verify the product gets synchronized on the next
        sync occurrence

        @id: 21efdd08-698c-443c-a681-edce19a4c83a

        @expectedresults: Product is synchronized successfully.

        @BZ: 1279539

        @CaseLevel: System
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        delay = 80
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'interval': 'hourly',
            'organization-id': self.org['id'],
            'sync-date': (
              datetime.utcnow() - timedelta(interval - delay/2)
            ).strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Verify product has not been synced yet
        self.logger.info('Waiting {0} seconds to check \
                product {1} was not synced'.format(delay/4, product['name']))
        sleep(delay/4)
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait until the first recurrence
        self.logger.info('Waiting {0} seconds to check \
                product {1} was synced'.format(delay, product['name']))
        sleep(delay)
        # Verify product was synced successfully
        self.validate_repo_content(
            repo, ['errata', 'package-groups', 'packages'])

    @tier4
    @upgrade
    def test_positive_synchronize_custom_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one custom
        product with it automatically.

        @id: 635bffe2-df98-4971-8950-40edc89e479e

        @expectedresults: Product is synchronized successfully.

        @CaseLevel: System
        """
        delay = 10 * 60  # delay for sync date in seconds
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'organization-id': self.org['id'],
            'sync-date': (datetime.utcnow() + timedelta(seconds=delay))
                        .strftime("%Y-%m-%d %H:%M:%S"),
        })
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        # Verify product is not synced and doesn't have any content
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Wait half of expected time
        self.logger.info('Waiting {0} seconds to check \
                product {1} was not synced'.format(delay/2, product['name']))
        sleep(delay/2)
        # Verify product has not been synced yet
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait the rest of expected time
        self.logger.info('Waiting {0} seconds to check \
                product {1} was synced'.format(delay/2, product['name']))
        sleep(delay/2)
        # Verify product was synced successfully
        self.validate_repo_content(
            repo, ['errata', 'package-groups', 'packages'])

    @tier4
    @upgrade
    def test_positive_synchronize_custom_products_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync multiple
        custom products with multiple repos automatically.

        @id: dd262cf3-b836-422c-baca-b3adbc532478

        @expectedresults: Products are synchronized successfully.

        @CaseLevel: System
        """
        delay = 10 * 60  # delay for sync date in seconds
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'organization-id': self.org['id'],
            'sync-date': (datetime.utcnow() + timedelta(seconds=delay))
                        .strftime("%Y-%m-%d %H:%M:%S"),
        })
        products = [
            make_product({'organization-id': self.org['id']})
            for _ in range(randint(3, 5))
        ]
        repos = [
            make_repository({'product-id': product['id']})
            for product in products
            for _ in range(randint(2, 3))
        ]
        # Verify products have not been synced yet
        for repo in repos:
            self.validate_repo_content(
                repo, ['errata', 'packages'], after_sync=False)
        # Associate sync plan with products
        for product in products:
            Product.set_sync_plan({
                'id': product['id'],
                'sync-plan-id': sync_plan['id'],
            })
        # Wait half of expected time
        self.logger.info('Waiting {0} seconds to check \
                products were synced'.format(delay/2))
        sleep(delay/2)
        # Verify products has not been synced yet
        for repo in repos:
            self.validate_repo_content(
                repo, ['errata', 'packages'], after_sync=False)
        # Wait the rest of expected time
        self.logger.info('Waiting {0} seconds to check \
                products were not synced'.format(delay/2))
        sleep(delay/2)
        # Verify product was synced successfully
        for repo in repos:
            self.validate_repo_content(
                repo, ['errata', 'package-groups', 'packages'])

    @run_in_one_thread
    @tier4
    @upgrade
    def test_positive_synchronize_rh_product_past_sync_date(self):
        """Create a sync plan with past datetime as a sync date, add a
        RH product and verify the product gets synchronized on the next sync
        occurrence

        @id: 47280ef4-3936-4dbc-8ed0-1076aa8d40df

        @expectedresults: Product is synchronized successfully.

        @BZ: 1279539

        @CaseLevel: System
        """
        interval = 60 * 60  # 'hourly' sync interval in seconds
        delay = 80
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': org['id'],
        })
        RepositorySet.enable({
            'name': REPOSET['rhva6'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
            'basearch': 'x86_64',
        })
        product = Product.info({
            'name': PRDS['rhel'],
            'organization-id': org['id'],
        })
        repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'product': product['name'],
            'organization-id': org['id'],
        })
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'interval': 'hourly',
            'organization-id': org['id'],
            'sync-date': (
              datetime.utcnow() - timedelta(interval - delay/2)
            ).strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Verify product has not been synced yet
        self.logger.info('Waiting {0} seconds to check \
                product {1} was not synced'.format(delay/4, product['name']))
        sleep(delay/4)
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait the rest of expected time
        self.logger.info('Waiting {0} seconds to check \
                product {1} was synced'.format(delay, product['name']))
        sleep(delay)
        # Verify product was synced successfully
        self.validate_repo_content(repo, ['errata', 'packages'])

    @run_in_one_thread
    @tier4
    @upgrade
    def test_positive_synchronize_rh_product_future_sync_date(self):
        """Create a sync plan with sync date in a future and sync one RH
        product with it automatically.

        @id: 6ce2f777-f230-4bb8-9822-2cf3580c21aa

        @expectedresults: Product is synchronized successfully.

        @CaseLevel: System
        """
        delay = 10 * 60  # delay for sync date in seconds
        org = make_org()
        with manifests.clone() as manifest:
            upload_file(manifest.content, manifest.filename)
        Subscription.upload({
            'file': manifest.filename,
            'organization-id': org['id'],
        })
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'organization-id': org['id'],
            'sync-date': (datetime.utcnow() + timedelta(seconds=delay))
                        .strftime("%Y-%m-%d %H:%M:%S"),
        })
        RepositorySet.enable({
            'name': REPOSET['rhva6'],
            'organization-id': org['id'],
            'product': PRDS['rhel'],
            'releasever': '6Server',
            'basearch': 'x86_64',
        })
        product = Product.info({
            'name': PRDS['rhel'],
            'organization-id': org['id'],
        })
        repo = Repository.info({
            'name': REPOS['rhva6']['name'],
            'product': product['name'],
            'organization-id': org['id'],
        })
        # Verify product is not synced and doesn't have any content
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Wait half of expected time
        self.logger.info('Waiting {0} seconds to check \
                product {1} was not synced'.format(delay/2, product['name']))
        sleep(delay/2)
        # Verify product has not been synced yet
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait the rest of expected time
        self.logger.info('Waiting {0} seconds to check \
                product {1} was synced'.format(delay/2, product['name']))
        sleep(delay/2)
        # Verify product was synced successfully
        self.validate_repo_content(repo, ['errata', 'packages'])

    @tier3
    @upgrade
    def test_positive_synchronize_custom_product_daily_recurrence(self):
        """Create a daily sync plan with a past datetime as a sync date,
        add a custom product and verify the product gets synchronized on
        the next sync occurrence

        @id: 8d882e8b-b5c1-4449-81c6-0efd31ad75a7

        @expectedresults: Product is synchronized successfully.

        @CaseLevel: System
        """
        delay = 300
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        start_date = datetime.utcnow() - timedelta(days=1)\
            + timedelta(seconds=delay/2)
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'interval': 'daily',
            'organization-id': self.org['id'],
            'sync-date': start_date.strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Verify product has not been synced yet
        self.logger.info('Waiting {0} seconds to check \
                product {1} was not synced'.format(delay/4, product['name']))
        sleep(delay/4)
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait until the first recurrence
        self.logger.info('Waiting {0} seconds to check \
                product {1} was synced'.format(delay, product['name']))
        sleep(delay)
        # Verify product was synced successfully
        self.validate_repo_content(
            repo, ['errata', 'package-groups', 'packages'])

    @skip_if_bug_open('bugzilla', '1463696')
    @tier3
    def test_positive_synchronize_custom_product_weekly_recurrence(self):
        """Create a weekly sync plan with a past datetime as a sync date,
        add a custom product and verify the product gets synchronized
        on the next sync occurrence

        @id: 1079a66d-7c23-44f6-a4a0-47f4c74d92a4

        @expectedresults: Product is synchronized successfully.

        @BZ: 1463696

        @CaseLevel: System
        """
        delay = 300
        product = make_product({'organization-id': self.org['id']})
        repo = make_repository({'product-id': product['id']})
        start_date = datetime.utcnow() - timedelta(weeks=1)\
            + timedelta(seconds=delay/2)
        sync_plan = self._make_sync_plan({
            'enabled': 'true',
            'interval': 'weekly',
            'organization-id': self.org['id'],
            'sync-date': start_date.strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Associate sync plan with product
        Product.set_sync_plan({
            'id': product['id'],
            'sync-plan-id': sync_plan['id'],
        })
        # Verify product has not been synced yet
        self.logger.info('Waiting {0} seconds to check \
                product {1} was not synced'.format(delay/4, product['name']))
        sleep(delay/4)
        self.validate_repo_content(
            repo, ['errata', 'packages'], after_sync=False)
        # Wait until the first recurrence
        self.logger.info('Waiting {0} seconds to check \
                product {1} was synced'.format(delay, product['name']))
        sleep(delay)
        # Verify product was synced successfully
        self.validate_repo_content(
            repo, ['errata', 'package-groups', 'packages'])
