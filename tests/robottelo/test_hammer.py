# -*- encoding: utf-8 -*-
"""Tests for Robottelo's hammer helpers"""
import unittest2

from robottelo.cli import hammer


class ParseCSVTestCase(unittest2.TestCase):
    """Tests for parsing CSV hammer output"""

    def test_parse_csv(self):
        output_lines = [
            u'Header,Header 2',
            u'header value 1,header with spaces value',
            u'MixEd CaSe ValUe,ALL CAPS VALUE',
            u'"""double quote escaped value""","," escaped value',
            u'unicode,chårs',
        ]
        self.assertEqual(
            hammer.parse_csv(output_lines),
            [
                {u'header': u'header value 1', u'header-2': u'header with spaces value'},
                {u'header': u'MixEd CaSe ValUe', u'header-2': u'ALL CAPS VALUE'},
                {u'header': u'"double quote escaped value"', u'header-2': u', escaped value'},
                {u'header': u'unicode', u'header-2': u'chårs'},
            ],
        )


class ParseJSONTestCase(unittest2.TestCase):
    """Tests for parsing JSON hammer output"""

    def test_parse_json(self):
        """Output generated with:
        hammer -u admin -p changeme --output json content-view info --id 1"""
        output = u"""{
          "ID": 1,
          "Name": "Default Organization View",
          "Label": "Default_Organization_View",
          "Composite": false,
          "Description": null,
          "Content Host Count": 0,
          "Organization": "Default Organization",
          "Yum Repositories": {
          },
          "Container Image Repositories": {
          },
          "OSTree Repositories": {
          },
          "Puppet Modules": {
          },
          "Lifecycle Environments": {
            "1": {
              "ID": 1,
              "Name": "Library"
            }
          },
          "Versions": {
            "1": {
              "ID": 1,
              "Version": "1.0",
              "Published": "2016-07-05 17:35:33 UTC"
            }
          },
          "Components": {
          },
          "Activation Keys": {
          }
        }"""

        self.assertEqual(
            hammer.parse_json(output),
            {
                u'puppet-modules': {},
                u'description': None,
                u'versions': {
                    u'1': {
                        u'version': u'1.0',
                        u'id': u'1',
                        u'published': u'2016-07-05 17:35:33 UTC',
                    }
                },
                u'composite': False,
                u'ostree-repositories': {},
                u'label': u'Default_Organization_View',
                u'activation-keys': {},
                u'container-image-repositories': {},
                u'components': {},
                u'organization': u'Default Organization',
                u'yum-repositories': {},
                u'lifecycle-environments': {u'1': {u'id': u'1', u'name': u'Library'}},
                u'id': u'1',
                u'content-host-count': u'0',
                u'name': u'Default Organization View',
            },
        )

    def test_parsed_json_match_parsed_csv(self):
        """ Output generated by:
        JSON:
        LANG=en_US.UTF-8  hammer -v -u admin -p changeme --output=json gpg
        info --id="160" --organization-id="1003"

        CSV:
        LANG=en_US.UTF-8  hammer -v -u admin -p changeme --output=csv gpg
        info --id="160" --organization-id="1003"
        """
        json_output = u"""{
          "ID": 160,
          "Name": "QUWTHo0WzF",
          "Organization": "ANtbiU",
          "Content": "qJxB1FX1UrssYiGGhRcZDF9eY8U"
        }
        """

        csv_ouput_lines = [
            u"ID,Name,Organization,Content",
            u"160,QUWTHo0WzF,ANtbiU,qJxB1FX1UrssYiGGhRcZDF9eY8U",
        ]

        self.assertEqual(hammer.parse_json(json_output), hammer.parse_csv(csv_ouput_lines)[0])


class ParseHelpTestCase(unittest2.TestCase):
    """Tests for parsing hammer help output"""

    def test_parse_help(self):
        """Can parse hammer help output"""
        self.maxDiff = None
        output = [
            'Usage:',
            '    hammer [OPTIONS] SUBCOMMAND [ARG] ...',
            '',
            'Parameters:',
            'SUBCOMMAND                    subcommand',
            '[ARG] ...                     subcommand arguments',
            '',
            'Subcommands:',
            ' activation-key                Manipulate activation keys.',
            ' capsule                       Manipulate capsule',
            ' compute-resource              Manipulate compute resources.',
            ' content-host                  Manipulate content hosts on the',
            '                               server',
            ' gpg                           Manipulate GPG Key actions on the',
            '                               server',
            'Options:',
            ' --autocomplete LINE           Get list of possible endings',
            ' --name, --deprecation-name    An option with a deprecation name',
            ' --csv                         Output as CSV (same as',
            '                               --output=csv)',
            ' --csv-separator SEPARATOR     Character to separate the values',
            ' --output ADAPTER              Set output format. One of [base,',
            '                               table, silent, csv, yaml, json]',
            ' -p, --password PASSWORD       password to access the remote',
            '                               system',
            ' -r, --reload-cache            force reload of Apipie cache',
        ]
        self.assertEqual(
            hammer.parse_help(output),
            {
                'subcommands': [
                    {'name': 'activation-key', 'description': 'Manipulate activation keys.'},
                    {'name': 'capsule', 'description': 'Manipulate capsule'},
                    {'name': 'compute-resource', 'description': 'Manipulate compute resources.'},
                    {
                        'name': 'content-host',
                        'description': ('Manipulate content hosts on the server'),
                    },
                    {'name': 'gpg', 'description': ('Manipulate GPG Key actions on the server')},
                ],
                'options': [
                    {
                        'name': 'autocomplete',
                        'shortname': None,
                        'value': 'LINE',
                        'help': 'Get list of possible endings',
                    },
                    {
                        'name': 'name',
                        'shortname': None,
                        'value': None,
                        'help': 'An option with a deprecation name',
                    },
                    {
                        'name': 'csv',
                        'shortname': None,
                        'value': None,
                        'help': 'Output as CSV (same as --output=csv)',
                    },
                    {
                        'name': 'csv-separator',
                        'shortname': None,
                        'value': 'SEPARATOR',
                        'help': 'Character to separate the values',
                    },
                    {
                        'name': 'output',
                        'shortname': None,
                        'value': 'ADAPTER',
                        'help': (
                            'Set output format. One of [base, table, silent, ' 'csv, yaml, json]'
                        ),
                    },
                    {
                        'name': 'password',
                        'shortname': 'p',
                        'value': 'PASSWORD',
                        'help': 'password to access the remote system',
                    },
                    {
                        'name': 'reload-cache',
                        'shortname': 'r',
                        'value': None,
                        'help': 'force reload of Apipie cache',
                    },
                ],
            },
        )


class ParseInfoTestCase(unittest2.TestCase):
    """Tests for parsing info hammer output"""

    def test_parse_simple(self):
        """Can parse a simple info output"""
        output = [
            'Id:                 19',
            'Full name:          4iv01o2u 10.5',
            'Release name:',
            '',
            'Family:',
            'Name:               4iv01o2u',
            'Major version:      10',
            'Minor version:      5',
        ]
        self.assertDictEqual(
            hammer.parse_info(output),
            {
                'id': '19',
                'full-name': '4iv01o2u 10.5',
                'release-name': {},
                'family': {},
                'name': '4iv01o2u',
                'major-version': '10',
                'minor-version': '5',
            },
        )

    def test_parse_numbered_list_attributes(self):
        """Can parse numbered list attributes"""
        output = ['Partition tables:', ' 1) ptable1', ' 2) ptable2', ' 3) ptable3', ' 4) ptable4']
        self.assertDictEqual(
            hammer.parse_info(output),
            {'partition-tables': ['ptable1', 'ptable2', 'ptable3', 'ptable4']},
        )

    def test_parse_list_attributes(self):
        """Can parse list attributes"""
        output = ['Partition tables:', ' ptable1', ' ptable2', ' ptable3', ' ptable4']
        self.assertDictEqual(
            hammer.parse_info(output),
            {'partition-tables': ['ptable1', 'ptable2', 'ptable3', 'ptable4']},
        )

    def test_parse_dict_attributes(self):
        """Can parse dict attributes"""
        output = [
            'Content:',
            ' 1) Repo Name: repo1',
            '    URL:       /custom/url1',
            ' 2) Repo Name: repo2',
            '    URL:       /custom/url2',
        ]
        self.assertDictEqual(
            hammer.parse_info(output),
            {
                'content': [
                    {'repo-name': 'repo1', 'url': '/custom/url1'},
                    {'repo-name': 'repo2', 'url': '/custom/url2'},
                ]
            },
        )

    def test_parse_info(self):
        """Can parse info output"""
        output = [
            'Sync State:   not_synced',
            'Sync Plan ID:',
            'GPG:',
            '    GPG Key ID: 1',
            '    GPG Key: key name',
            'Organizations:',
            '    1) Org 1',
            '    2) Org 2',
            'Locations:',
            '    Loc 1',
            '    Loc 2',
            'Repositories:',
            ' 1) Repo Name: repo1',
            '    Repo ID:   10',
            ' 2) Repo Name: repo2',
            '    Repo ID:   20',
            ' 3) Repo Name => repo3',
            '    Repo ID =>   30',
        ]
        self.assertEqual(
            hammer.parse_info(output),
            {
                'sync-state': 'not_synced',
                'sync-plan-id': {},
                'gpg': {'gpg-key-id': '1', 'gpg-key': 'key name'},
                'organizations': ['Org 1', 'Org 2'],
                'locations': ['Loc 1', 'Loc 2'],
                'repositories': [
                    {'repo-id': '10', 'repo-name': 'repo1'},
                    {'repo-id': '20', 'repo-name': 'repo2'},
                    {'repo-id': '30', 'repo-name': 'repo3'},
                ],
            },
        )

    def test_parse(self):
        """Can parse actual host info"""
        output = [
            'Id: 31',
            'Name: name1',
            'Organization: org1',
            'Location: Default Location',
            'Cert name: cert name',
            'Managed: no',
            'Installed at:',
            'Last report:',
            'Uptime (seconds): 67',
            'Status:',
            '    Global Status: Error',
            'Network:',
            '    IPv4 address: ip1',
            '    MAC: mac1',
            '    Domain: domain1',
            'Network interfaces:',
            ' 1) Id: 34',
            '    Identifier: ens3',
            '    Type: interface (primary, provision)',
            '    MAC address: mac2',
            '    IPv4 address: ip2',
            '    FQDN: name1.domain',
            'Operating system:',
            '    Architecture: x86_64',
            '    Operating System: os1',
            '    Build: no',
            '    Custom partition table:',
            'Parameters:',
            '',
            'All parameters:',
            '    enable-puppet5 => true',
            '    enable-epel => false',
            'Additional info:',
            '    Owner: Anonymous Admin',
            '    Owner Type: User',
            '    Enabled: yes',
            '    Model: Standard PC (i440FX + PIIX, 1996)',
            '    Comment:',
            'OpenSCAP Proxy:',
            'Content Information:',
            '    Content View:',
            '        ID: 38',
            '        Name: content view1',
            '    Lifecycle Environment:',
            '        ID: 40',
            '        Name: lifecycle environment1',
            '    Content Source:',
            '        ID:',
            '        Name:',
            '    Kickstart Repository:',
            '        ID:',
            '        Name:',
            '    Applicable Packages: 0',
            '    Upgradable Packages: 0',
            '    Applicable Errata:',
            '        Enhancement: 0',
            '        Bug Fix: 0',
            '        Security: 0',
            'Subscription Information:',
            '    UUID: uuid1',
            '    Last Checkin: 2019-12-13 00:00:00 UTC',
            '    Release Version:',
            '    Autoheal: true',
            '    Registered To: tier3',
            '    Registered At: 2019-12-13 00:00:00 UTC',
            '    Registered by Activation Keys:',
            '     1) ak1',
            '    System Purpose:',
            '        Service Level:',
            '        Purpose Usage:',
            '        Purpose Role:',
            '        Purpose Addons:',
            'Host Collections:',
        ]
        self.assertEqual(
            hammer.parse_info(output),
            {
                'id': '31',
                'name': 'name1',
                'organization': 'org1',
                'location': 'Default Location',
                'cert-name': 'cert name',
                'managed': 'no',
                'installed-at': {},
                'last-report': {},
                'uptime-(seconds)': '67',
                'status': {'global-status': 'Error'},
                'network': {'ipv4-address': 'ip1', 'mac': 'mac1', 'domain': 'domain1'},
                'network-interfaces': [
                    {
                        'id': '34',
                        'identifier': 'ens3',
                        'type': 'interface (primary, provision)',
                        'mac-address': 'mac2',
                        'ipv4-address': 'ip2',
                        'fqdn': 'name1.domain',
                    }
                ],
                'operating-system': {
                    'architecture': 'x86_64',
                    'operating-system': 'os1',
                    'build': 'no',
                    'custom-partition-table': '',
                },
                'parameters': {},
                'all-parameters': {'enable-puppet5': 'true', 'enable-epel': 'false'},
                'additional-info': {
                    'owner': 'Anonymous Admin',
                    'owner-type': 'User',
                    'enabled': 'yes',
                    'model': 'Standard PC (i440FX + PIIX, 1996)',
                    'comment': '',
                },
                'openscap-proxy': {},
                'content-information': {
                    'content-view': {'id': '38', 'name': 'content view1'},
                    'lifecycle-environment': {'id': '40', 'name': 'lifecycle environment1'},
                    'content-source': {'id': '', 'name': ''},
                    'kickstart-repository': {'id': '', 'name': ''},
                    'applicable-packages': '0',
                    'upgradable-packages': '0',
                    'applicable-errata': {'enhancement': '0', 'bug-fix': '0', 'security': '0'},
                },
                'subscription-information': {
                    'uuid': 'uuid1',
                    'last-checkin': '2019-12-13 00:00:00 UTC',
                    'release-version': '',
                    'autoheal': 'true',
                    'registered-to': 'tier3',
                    'registered-at': '2019-12-13 00:00:00 UTC',
                    'registered-by-activation-keys': ['ak1'],
                    'system-purpose': {
                        'service-level': '',
                        'purpose-usage': '',
                        'purpose-role': '',
                        'purpose-addons': '',
                    },
                },
                'host-collections': {},
            },
        )

    def test_parse_json_list(self):
        """Can parse a list in json"""
        self.assertEqual(hammer.parse_json('["item1", "item2"]'), ['item1', 'item2'])
