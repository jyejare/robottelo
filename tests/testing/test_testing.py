"""Test math sqrt module works

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: jyejare

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade


class TestTheUpgradeTesting2:
    """Verify something can be done after upgrade.

    :id: 150142c9-a32a-48e6-a16d-0af5d497cee1

    :steps:
        1. Step 1
        2. Step 2
        3. Step 3
        4. Upgrade satellite.
        5. Final Step

    :expectedresults: Expected results success.
    """

    @pytest.fixture(scope='function')
    def sixteens_sqroot(self, request):
        """
        The purpose of this fixture is to setup the activation key based on the provided
        organization, content_view and activation key name.
        """
        import math
        return math.sqrt(16)

    @pre_upgrade
    @pytest.mark.parametrize(
        'sixteens_sqroot', ['test_pre_part'], indirect=True
    )
    def test_pre_part(self, sixteens_sqroot):
        """The pre upgrade def to do the pre upgrade stuff."""
        assert sixteens_sqroot == 4

    @post_upgrade(depend_on=test_pre_part)
    def test_past_part(self, dependent_scenario_name):
        """ The post upgrade def to do the post upgrade stuff.
        """
        import math
        assert math.sqrt(25) == 5


class TestTheUpgradeOnlyPre:
    """Verify something can be done just before upgrade

    :id: d0b44b1f-fd1a-480a-b898-8d4655bf651c

    :steps:
        1. Step 1
        2. Step 2
        3. Upgrade satellite

    :expectedresults: upgrade success
    """

    @pytest.fixture(scope='function')
    def tsix_sqroot(self, request):
        """
        The purpose of this fixture is to setup the activation key based on the provided
        organization, content_view and activation key name.
        """
        import math
        return math.sqrt(36)

    @pre_upgrade
    @pytest.mark.parametrize(
        'tsix_sqroot', ['test_pre_part'], indirect=True
    )
    def test_pre_part(self, tsix_sqroot):
        """The pre upgrade def to do the pre upgrade stuff."""
        assert tsix_sqroot == 6