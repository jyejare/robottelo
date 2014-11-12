"""Data-driven unit tests for multiple paths."""
from ddt import data, ddt
from functools import partial
from requests.exceptions import HTTPError
from robottelo.api import client
from robottelo.common import conf
from robottelo.common.decorators import (
    bz_bug_is_open, run_only_on, skip_if_bug_open)
from robottelo.common.helpers import get_server_credentials
from robottelo import entities
from unittest import TestCase
import httplib
import logging
# (too-many-public-methods) pylint:disable=R0904


logger = logging.getLogger(__name__)  # pylint:disable=C0103


BZ_1118015_ENTITIES = (
    entities.ActivationKey, entities.Architecture, entities.ComputeResource,
    entities.ConfigTemplate, entities.ContentView, entities.Environment,
    entities.GPGKey, entities.Host, entities.HostCollection,
    entities.LifecycleEnvironment, entities.OperatingSystem, entities.Product,
    entities.Repository, entities.Role, entities.Subnet, entities.System,
    entities.User,
)
BZ_1151240_ENTITIES = (
    entities.ActivationKey, entities.ContentView, entities.GPGKey,
    entities.LifecycleEnvironment, entities.Product, entities.Repository
)
BZ_1154156_ENTITIES = (entities.ConfigTemplate, entities.Host, entities.User)


def _get_partial_func(obj):
    """Return ``obj.func`` if ``obj`` is a partial, or ``obj`` otherwise."""
    if isinstance(obj, partial):
        return obj.func
    return obj


def skip_if_sam(self, entity):
    """Skip test if testing sam features and entity is unavailable in sam.

    Usage::

        def test_sample_test(self, entity):
            skip_if_sam(self, entity)
            # test code continues here

    The above code snippet skips the test when:

    * ``robottelo.properties`` is defined with ``main.project=sam``, and
    * the corresponding entity's definition in :mod:`robottelo.entities` does
      not specify sam in server_modes. For example: ``server_modes = ('sat')``.

    :param entity: One of the entities defined in :meth:`robottelo.entities`.
    :returns: Either ``self.skipTest`` or ``None``.

    """
    robottelo_mode = conf.properties.get('main.project', '').lower()
    server_modes = [
        server_mode.lower()
        for server_mode
        in _get_partial_func(entity).Meta.server_modes
    ]

    if robottelo_mode == 'sam' and 'sam' not in server_modes:
        return self.skipTest(
            'Server runs in "{0}" mode and this entity is associated only to '
            '"{1}" mode(s).'.format(robottelo_mode, "".join(server_modes))
        )

    # else just return - do nothing!


@ddt
class EntityTestCase(TestCase):
    """Issue HTTP requests to various ``entity/`` paths."""
    _multiprocess_can_split_ = True

    @data(
        # entities.ActivationKey,  # need organization_id or environment_id
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        entities.ComputeResource,
        entities.ConfigTemplate,
        # entities.ContentView,  # need organization_id
        entities.Domain,
        entities.Environment,
        # entities.GPGKey,  # need organization_id
        entities.Host,
        # entities.HostCollection,  # need organization_id
        # entities.LifecycleEnvironment,  # need organization_id
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        # entities.Product,  # need organization_id
        # entities.Repository,  # need organization_id
        entities.Role,
        entities.Subnet,
        # entities.System,  # need organization_id
        entities.TemplateKind,
        entities.User,
    )
    def test_get_status_code(self, entity_cls):
        """@Test GET an entity-dependent path.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        logger.debug('test_get_status_code arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        response = entity_cls().read_raw()
        self.assertEqual(httplib.OK, response.status_code)
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        # entities.ActivationKey,  # need organization id or environment id
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        entities.ComputeResource,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        entities.System,
        entities.TemplateKind,
        entities.User,
    )
    def test_get_unauthorized(self, entity_cls):
        """@Test: GET an entity-dependent path without credentials.

        @Assert: HTTP 401 is returned

        """
        logger.debug('test_get_unauthorized arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        response = entity_cls().read_raw(auth=())
        self.assertEqual(httplib.UNAUTHORIZED, response.status_code)

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        partial(entities.ComputeResource, provider='EC2'),
        partial(entities.ComputeResource, provider='GCE'),
        partial(entities.ComputeResource, provider='Libvirt'),
        partial(entities.ComputeResource, provider='Openstack'),
        partial(entities.ComputeResource, provider='Ovirt'),
        partial(entities.ComputeResource, provider='Rackspace'),
        partial(entities.ComputeResource, provider='Vmware'),
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        entities.System,
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_post_status_code(self, entity_cls):
        """@Test: Issue a POST request and check the returned status code.

        @Assert: HTTP 201 is returned with an ``application/json`` content-type

        """
        logger.debug('test_post_status_code arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)

        # Some arguments are "normal" classes and others are objects produced
        # by functools.partial. Also, `partial(SomeClass).func == SomeClass`.
        if (_get_partial_func(entity_cls) in BZ_1118015_ENTITIES and
                bz_bug_is_open(1118015)):
            self.skipTest('Bugzilla bug 1118015 is open.')

        response = entity_cls().create_raw()
        self.assertEqual(httplib.CREATED, response.status_code)
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        entities.ComputeResource,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        entities.System,
        entities.TemplateKind,
        entities.User,
    )
    @skip_if_bug_open('bugzilla', 1122257)
    def test_post_unauthorized(self, entity_cls):
        """@Test: POST to an entity-dependent path without credentials.

        @Assert: HTTP 401 is returned

        """
        logger.debug('test_post_unauthorized arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        self.assertEqual(
            httplib.UNAUTHORIZED,
            entity_cls().create_raw(auth=(), create_missing=False).status_code
        )


@ddt
class EntityIdTestCase(TestCase):
    """Issue HTTP requests to various ``entity/:id`` paths."""
    _multiprocess_can_split_ = True

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        partial(entities.ComputeResource, provider='Libvirt'),
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_get_status_code(self, entity_cls):
        """@Test: Create an entity and GET it.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        logger.debug('test_get_status_code arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        try:
            entity = entity_cls(id=entity_cls().create_json()['id'])
        except HTTPError as err:
            self.fail(err)
        response = entity.read_raw()
        self.assertEqual(httplib.OK, response.status_code)
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        partial(entities.ComputeResource, provider='Libvirt'),
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_put_status_code(self, entity_cls):
        """@Test Issue a PUT request and check the returned status code.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        logger.debug('test_put_status_code arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        if entity_cls in BZ_1154156_ENTITIES and bz_bug_is_open(1154156):
            self.skipTest("Bugzilla bug 1154156 is open.")

        # Create an entity
        entity = entity_cls(id=entity_cls().create_json()['id'])

        # Update that entity.
        entity.create_missing()
        response = client.put(
            entity.path(),
            entity.create_payload(),  # FIXME: use entity.update_payload()
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertEqual(httplib.OK, response.status_code)
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        partial(entities.ComputeResource, provider='Libvirt'),
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_delete_status_code(self, entity_cls):
        """@Test Issue an HTTP DELETE request and check the returned status
        code.

        @Assert: HTTP 200, 202 or 204 is returned with an ``application/json``
        content-type.

        """
        logger.debug('test_delete_status_code arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        if entity_cls is entities.ConfigTemplate and bz_bug_is_open(1096333):
            self.skipTest('Cannot delete config templates.')
        try:
            entity = entity_cls(id=entity_cls().create_json()['id'])
        except HTTPError as err:
            self.fail(err)
        response = client.delete(
            entity.path(),
            auth=get_server_credentials(),
            verify=False,
        )
        self.assertIn(
            response.status_code,
            (httplib.NO_CONTENT, httplib.OK, httplib.ACCEPTED)
        )

        # According to RFC 2616, HTTP 204 responses "MUST NOT include a
        # message-body". If a message does not have a body, there is no need to
        # set the content-type of the message.
        if response.status_code is not httplib.NO_CONTENT:
            self.assertIn('application/json', response.headers['content-type'])


@ddt
class DoubleCheckTestCase(TestCase):
    """Perform in-depth tests on URLs.

    Do not just assume that an HTTP response with a good status code indicates
    that an action succeeded. Instead, issue a follow-up request after each
    action to ensure that the intended action was accomplished.

    """
    _multiprocess_can_split_ = True
    longMessage = True

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        partial(entities.ComputeResource, provider='Libvirt'),
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_put_and_get(self, entity_cls):
        """@Test: Issue a PUT request and GET the updated entity.

        @Assert: The updated entity has the correct attributes.

        """
        logger.debug('test_put_and_get arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        if entity_cls in BZ_1154156_ENTITIES and bz_bug_is_open(1154156):
            self.skipTest("Bugzilla bug 1154156 is open.")

        # Create an entity.
        entity = entity_cls(id=entity_cls().create_json()['id'])

        # Update that entity.
        entity.create_missing()
        payload = entity.create_payload()  # FIXME: use entity.update_payload()
        response = client.put(
            entity.path(),
            payload,
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()

        # Drop the extra outer dict and sensitive params from `payload`.
        if len(payload.keys()) == 1 and isinstance(payload.values()[0], dict):
            payload = payload.values()[0]
        if isinstance(entity, entities.Host):
            del payload['root_pass']
            del payload['name']  # FIXME: "Foo" in, "foo.example.com" out.
        if issubclass(_get_partial_func(entity_cls), entities.User):
            del payload['password']

        # It is impossible to easily verify foreign keys.
        if bz_bug_is_open(1151240):
            for key in payload.keys():
                if key.endswith('_id') or key.endswith('_ids'):
                    del payload[key]
            if issubclass(
                    _get_partial_func(entity_cls),
                    entities.LifecycleEnvironment):
                del payload['prior']  # this foreign key is oddly named

        # Compare a trimmed-down `payload` against what the server has.
        attrs = entity.read_json()
        for key, value in payload.items():
            self.assertIn(key, attrs.keys())
            self.assertEqual(value, attrs[key], key)

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        partial(entities.ComputeResource, provider='Libvirt'),
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_post_and_get(self, entity_cls):
        """@Test Issue a POST request and GET the created entity.

        @Assert: The created entity has the correct attributes.

        """
        logger.debug('test_post_and_get arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        if entity_cls in BZ_1151240_ENTITIES and bz_bug_is_open(1151240):
            self.skipTest("Bugzilla bug 1151240 is open.""")
        if entity_cls in BZ_1154156_ENTITIES and bz_bug_is_open(1154156):
            self.skipTest("Bugzilla bug 1154156 is open.")

        # Create an entity.
        entity = entity_cls()
        entity.id = entity.create_json()['id']

        # Drop the extra outer dict and sensitive params from `payload`.
        payload = entity.create_payload()
        if len(payload.keys()) == 1 and isinstance(payload.values()[0], dict):
            payload = payload.values()[0]
        if isinstance(entity, entities.Host):
            del payload['root_pass']
            del payload['name']  # FIXME: "Foo" in, "foo.example.com" out.
        if isinstance(entity, entities.User):
            del payload['password']

        # It is impossible to easily verify foreign keys.
        if bz_bug_is_open(1151240):
            for key in payload.keys():
                if key.endswith('_id') or key.endswith('_ids'):
                    del payload[key]

        # Compare a trimmed-down `payload` against what the server has.
        attrs = entity.read_json()
        for key, value in payload.items():
            self.assertIn(key, attrs.keys())
            self.assertEqual(value, attrs[key], key)

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        partial(entities.ComputeResource, provider='Libvirt'),
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_delete_and_get(self, entity_cls):
        """@Test: Issue an HTTP DELETE request and GET the deleted entity.

        @Assert: An HTTP 404 is returned when fetching the missing entity.

        """
        logger.debug('test_delete_and_get arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        if entity_cls is entities.ConfigTemplate and bz_bug_is_open(1096333):
            self.skipTest('Cannot delete config templates.')

        # Create an entity, delete it and get it.
        try:
            entity = entity_cls(id=entity_cls().create_json()['id'])
        except HTTPError as err:
            self.fail(err)
        entity.delete()

        if entity_cls is entities.Repository and bz_bug_is_open(1163494):
            return
        self.assertEqual(httplib.NOT_FOUND, entity.read_raw().status_code)


@ddt
class EntityReadTestCase(TestCase):
    """
    Check that classes inheriting from :class:`robottelo.orm.EntityReadMixin`
    function correctly.
    """
    _multiprocess_can_split_ = True

    # Most entities are commented-out because they do not inherit from
    # EntityReadMixin, due to issues with data returned from the API.
    #
    # ComputeResource entities cannot be reliably read because, depending upon
    # the provider, different sets of attributes are returned. For example, the
    # "uuid" attribute is only returned for certain providers. Perhaps multiple
    # types of compute resources should be created? For example:
    # LibvirtComputeResource.
    @data(
        # entities.ActivationKey,
        # entities.Architecture,  # see test_architecture_read
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        # partial(entities.ComputeResource, provider='Libvirt'),
        # entities.ConfigTemplate,
        # entities.ContentView,
        # entities.Domain,
        entities.Environment,
        # entities.GPGKey,
        # entities.Host,  # FIXME: investigate this
        entities.HostCollection,
        # entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        # entities.OperatingSystemParameter,  # see test_osparameter_read
        entities.Organization,
        # entities.Product,
        entities.Repository,
        entities.Role,
        # entities.Subnet,  # "domains" attribute is useless when reading.
        # entities.System,
        # entities.TemplateKind,  # see comments in class definition
        # entities.User,
    )
    def test_entity_read(self, entity_cls):
        """@Test: Create an entity and get it using
        :meth:`robottelo.orm.EntityReadMixin.read`.

        @Assert: The just-read entity is an instance of the correct class.

        """
        logger.debug('test_entity_read arg: {0}'.format(entity_cls))
        skip_if_sam(self, entity_cls)
        entity_id = entity_cls().create_json()['id']
        self.assertIsInstance(entity_cls(id=entity_id).read(), entity_cls)

    def test_architecture_read(self):
        """@Test: Create an arch that points to an OS, and read the arch.

        @Assert: The call to :meth:`robottelo.entities.Architecture.read`
        succeeds, and the response contains the correct operating system ID.

        """
        os_id = entities.OperatingSystem().create_json()['id']
        arch_id = entities.Architecture(
            operatingsystem=[os_id]
        ).create_json()['id']
        architecture = entities.Architecture(id=arch_id).read()
        self.assertEqual(len(architecture.operatingsystem), 1)
        self.assertEqual(architecture.operatingsystem[0].id, os_id)

    @run_only_on('sat')
    def test_osparameter_read(self):
        """@Test: Create an OperatingSystemParameter and get it using
        :meth:`robottelo.orm.EntityReadMixin.read`.

        @Assert: The just-read entity is an instance of the correct class.

        """
        os_attrs = entities.OperatingSystem().create_json()
        osp_attrs = entities.OperatingSystemParameter(
            os_attrs['id']
        ).create_json()
        self.assertIsInstance(
            entities.OperatingSystemParameter(
                os_attrs['id'],
                id=osp_attrs['id'],
            ).read(),
            entities.OperatingSystemParameter
        )

    @run_only_on('sat')
    def test_permission_read(self):
        """@Test: Create an Permission entity and get it using
        :meth:`robottelo.orm.EntityReadMixin.read`.

        @Assert: The just-read entity is an instance of the correct class and
        name and resource_type fields are populated

        """
        attrs = entities.Permission().search(per_page=1)[0]
        read_entity = entities.Permission(id=attrs['id']).read()
        self.assertIsInstance(read_entity, entities.Permission)
        self.assertGreater(len(read_entity.name), 0)
        self.assertGreater(len(read_entity.resource_type), 0)

    def test_media_read(self):
        """@Test: Create a media pointing at an OS and read the media.

        @Assert: The media points at the correct operating system.

        """
        os_id = entities.OperatingSystem().create_json()['id']
        media_id = entities.Media(operatingsystem=[os_id]).create_json()['id']
        media = entities.Media(id=media_id).read()
        self.assertEqual(len(media.operatingsystem), 1)
        self.assertEqual(media.operatingsystem[0].id, os_id)
