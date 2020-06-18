# -*- coding: utf-8 -*-
"""Tests for testing manual upload

:Requirement: TestingManualUploads

:CaseAutomation: NotAutomated

:CaseLevel: Component

:CaseComponent: ProvisioningTemplates

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from robottelo.decorators import stubbed, tier1, tier2, tier3

@tier1
def test_1():
    """This is test1

    :id: 7f551e69-32d0-4877-9275-ac1f9f821d7d

    :Steps: I have only one test

    :expectedresults: Assert correct
    """
    assert 2 == 2

@tier1
def test_11():
    """This is test1

    :id: 7bd28427-45d6-4305-873c-a9f19c3a1c64

    :Steps: I have only one test

    :expectedresults: Assert correct
    """
    assert 2 == 5

@tier2
@pytest.mark.stubbed
def test_2():
    """This is test2

    :id: da45a583-7066-4fdb-96a6-e5b2b5f4fe08

    :Steps: I have only one test2

    :expectedresults: Assert correct2
    """
    pass

@tier2
def test_22():
    """This is test2

    :id: 5b437660-4421-41c6-b8f7-ca84fa393580

    :Steps: I have only one test2

    :expectedresults: Assert correct2
    """
    assert 6*7 == 42

@tier3
def test_3():
    """This is test2

    :id: 9064009f-fd7a-41ad-99ae-16536305236c

    :Steps: I have only one test2

    :expectedresults: Assert correct2
    """
    assert 'Love' == 'Hate'

@tier3
def test_33():
    """This is test2

    :id: efef9f1e-0b2a-4305-8ee6-e1320a297a56

    :Steps: I have only one test2

    :expectedresults: Assert correct2
    """
    pytest.skip()
