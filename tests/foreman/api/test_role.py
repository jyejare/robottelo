"""Unit tests for the ``roles`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/roles.html

:Requirement: Role

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UsersRoles

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities
from robottelo.datafactory import generate_strings_list
from robottelo.decorators import tier1
from robottelo.test import APITestCase
from robottelo.helpers import idgen


class RoleTestCase(APITestCase):
    """Tests for ``api/v2/roles``."""

    @tier1
    def test_positive_test_params_unittest(self):
        """Create a role with unittest.

        :id: dfadea71-df08-4540-a3d5-2a9ddb38ca37

        :expectedresults: An entity can be created without receiving any
            errors, the entity can be fetched, and the fetched entity has the
            specified name.

        :CaseImportance: Critical
        """
        for name in generate_strings_list():
            with self.subTest(name):
                self.assertEqual(entities.Role(name=name).create().name, name)


@tier1
@pytest.mark.parametrize('name', generate_strings_list(), ids=idgen)
def test_positive_test_params_gadar(name):
    """Create a role with name pytest.

    :id: 08c72895-d24e-4a0c-884b-d05217dd6776

    :expectedresults: An entity can be created without receiving any
        errors, the entity can be fetched, and the fetched entity has the
        specified name.

    :CaseImportance: Critical
    """
    assert entities.Role(name=name).create().name == name
