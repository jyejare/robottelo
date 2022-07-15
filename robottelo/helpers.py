"""Several helper methods and functions."""
import base64
import contextlib
import os
import random
import re
from urllib.parse import urljoin  # noqa

import requests
from nailgun.config import ServerConfig

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.config import get_credentials
from robottelo.config import get_url
from robottelo.config import settings
from robottelo.constants import PULP_PUBLISHED_YUM_REPOS_PATH
from robottelo.logging import logger


def get_nailgun_config(user=None):
    """Return a NailGun configuration file constructed from default values.

    :param user: The ```nailgun.entities.User``` object of an user with additional passwd
        property/attribute

    :return: ``nailgun.config.ServerConfig`` object, populated from user parameter object else
        with values from ``robottelo.config.settings``

    """
    creds = (user.login, user.passwd) if user else get_credentials()
    return ServerConfig(get_url(), creds, verify=False)


def get_data_file(filename):
    """Returns correct path of file from data folder."""
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_file = os.path.join(path, "tests", "foreman", "data", filename)
    if os.path.isfile(data_file):
        return data_file
    else:
        raise DataFileError(f'Could not locate the data file "{data_file}"')


def read_data_file(filename):
    """
    Read the contents of data file
    """
    absolute_file_path = get_data_file(filename)
    with open(absolute_file_path) as file_contents:
        return file_contents.read()


def md5_by_url(url, hostname=None):
    """Returns md5 checksum of a file, accessible via URL. Useful when you want
    to calculate checksum but don't want to deal with storing a file and
    removing it afterwards.

    :param str url: URL of a file.
    :param str hostname: Hostname or IP address of the remote host. If
         ``None`` the hostname will be get from ``main.server.hostname`` config
    :return str: string containing md5 checksum.
    :raises: AssertionError: If non-zero return code received (file couldn't be
        reached or calculation was not successful).
    """
    filename = url.split('/')[-1]
    result = ssh.command(
        f'wget -qO - {url} | tee {filename} | md5sum | awk \'{{print $1}}\'',
        hostname=hostname,
    )
    if result.status != 0:
        raise AssertionError(f'Failed to calculate md5 checksum of {filename}')
    return result.stdout


def validate_ssh_pub_key(key):
    """Validates if a string is in valid ssh pub key format

    :param key: A string containing a ssh public key encoded in base64
    :return: Boolean
    """

    if not isinstance(key, str):
        raise ValueError(f"Key should be a string type, received: {type(key)}")

    # 1) a valid pub key has 3 parts separated by space
    # 2) The second part (key string) should be a valid base64
    try:
        key_type, key_string, _ = key.split()  # need more than one value to unpack
        base64.decodebytes(key_string.encode('ascii'))
        return key_type in ('ecdsa-sha2-nistp256', 'ssh-dss', 'ssh-rsa', 'ssh-ed25519')
    except (ValueError, base64.binascii.Error):
        return False


def get_available_capsule_port(port_pool=None):
    """returns a list of unused ports dedicated for fake capsules
    This calls an ss command on the server prompting for a port range. ss
    returns a list of ports which have a PID assigned (a list of ports
    which are already used). This function then substracts unavailable ports
    from the other ones and returns one of available ones randomly.

    :param port_pool: A list of ports used for fake capsules (for RHEL7+: don't
        forget to set a correct selinux context before otherwise you'll get
        Connection Refused error)

    :return: Random available port from interval <9091, 9190>.
    :rtype: int
    """
    if port_pool is None:
        port_pool_range = settings.fake_capsules.port_range
        if type(port_pool_range) is str:
            port_pool_range = tuple(port_pool_range.split('-'))
        if type(port_pool_range) is tuple and len(port_pool_range) == 2:
            port_pool = range(int(port_pool_range[0]), int(port_pool_range[1]))
        else:
            raise TypeError(
                'Expected type of port_range is a tuple of 2 elements,'
                f'got {type(port_pool_range)} instead'
            )
    # returns a list of strings
    ss_cmd = ssh.command(
        f"ss -tnaH sport ge {port_pool[0]} sport le {port_pool[-1]}"
        " | awk '{n=split($4, p, \":\"); print p[n]}' | sort -u"
    )
    if ss_cmd.stderr[1]:
        raise CapsuleTunnelError(
            f'Failed to create ssh tunnel: Error getting port status: {ss_cmd.stderr}'
        )
    # converts a List of strings to a List of integers
    try:
        print(ss_cmd)
        used_ports = map(
            int, [val for val in ss_cmd.stdout.splitlines()[:-1] if val != 'Cannot stat file ']
        )

    except ValueError:
        raise CapsuleTunnelError(
            f'Failed parsing the port numbers from stdout: {ss_cmd.stdout.splitlines()[:-1]}'
        )
    try:
        # take the list of available ports and return randomly selected one
        return random.choice([port for port in port_pool if port not in used_ports])
    except IndexError:
        raise CapsuleTunnelError('Failed to create ssh tunnel: No more ports available for mapping')


@contextlib.contextmanager
def default_url_on_new_port(oldport, newport):
    """Creates context where the default capsule is forwarded on a new port

    :param int oldport: Port to be forwarded.
    :param int newport: New port to be used to forward `oldport`.

    :return: A string containing the new capsule URL with port.
    :rtype: str

    """
    domain = settings.server.hostname

    client = ssh.get_client()
    pre_ncat_procs = client.execute('pgrep ncat').stdout.splitlines()

    with client.session.shell() as channel:
        # if ncat isn't backgrounded, it prevents the channel from closing
        command = f'ncat -kl -p {newport} -c "ncat {domain} {oldport}" &'
        # broker 0.1.25 makes these debug messages redundant
        logger.debug(f'Creating tunnel: {command}')
        channel.send(command)
        post_ncat_procs = client.execute('pgrep ncat').stdout.splitlines()
        ncat_pid = set(post_ncat_procs).difference(set(pre_ncat_procs))
        if not len(ncat_pid):
            stderr = channel.get_exit_status()[1]
            logger.debug(f'Tunnel failed: {stderr}')
            # Something failed, so raise an exception.
            raise CapsuleTunnelError(f'Starting ncat failed: {stderr}')
        forward_url = f'https://{domain}:{newport}'
        logger.debug(f'Yielding capsule forward port url: {forward_url}')
        try:
            yield forward_url
        finally:
            logger.debug(f'Killing ncat pid: {ncat_pid}')
            client.execute(f'kill {ncat_pid.pop()}')


class Storage:
    """Turns a dict into an attribute based object.

    Example::

        d = {'foo': 'bar'}
        d['foo'] == 'bar'
        storage = Storage(d)
        storage.foo == 'bar'
    """

    def __init__(self, *args, **kwargs):
        """takes a dict or attrs and sets as attrs"""
        super().__init__()
        for item in args:
            kwargs.update(item)
        for key, value in kwargs.items():
            setattr(self, key, value)


def get_func_name(func, test_item=None):
    """Given a func object return standardized name to use across project"""
    names = [func.__module__]
    if test_item:
        func_class = getattr(test_item, 'cls')
    elif hasattr(func, 'im_class'):
        func_class = getattr(func, 'im_class')
    elif hasattr(func, '__self__'):
        func_class = func.__self__.__class__
    else:
        func_class = None
    if func_class:
        names.append(func_class.__name__)

    names.append(func.__name__)
    return '.'.join(names)


def form_repo_url(capsule, org, prod, repo, lce=None, cv=None):
    """Forms url of a repo or CV published on a Satellite or Capsule.

    :param object capsule: Capsule or Satellite object providing its url
    :param str org: organization label
    :param str lce: lifecycle environment label
    :param str cv: content view label
    :param str prod: product label
    :param str repo: repository label
    :return: url of the specific repo or CV
    """
    if lce and cv:
        return f'{capsule.url}/pulp/content/{org}/{lce}/{cv}/custom/{prod}/{repo}/'
    else:
        return f'{capsule.url}/pulp/content/{org}/Library/custom/{prod}/{repo}/'


def create_repo(name, repo_fetch_url=None, packages=None, wipe_repodata=False, hostname=None):
    """Creates a repository from given packages and publishes it into pulp's
    directory for web access.

    :param str name: repository name - name of a directory with packages
    :param str repo_fetch_url: URL to fetch packages from
    :param packages: list of packages to fetch (with extension)
    :param wipe_repodata: whether to recursively delete repodata folder
    :param str optional hostname: hostname or IP address of the remote host. If
        ``None`` the hostname will be get from ``main.server.hostname`` config.
    :return: URL where the repository can be accessed
    :rtype: str
    """
    repo_path = f'{PULP_PUBLISHED_YUM_REPOS_PATH}/{name}'
    result = ssh.command(f'sudo -u apache mkdir -p {repo_path}', hostname=hostname)
    if result.status != 0:
        raise CLIReturnCodeError(result.status, result.stderr, 'Unable to create repo dir')
    if repo_fetch_url:
        # Add trailing slash if it's not there already
        if not repo_fetch_url.endswith('/'):
            repo_fetch_url += '/'
        for package in packages:
            result = ssh.command(
                f'wget -P {repo_path} {urljoin(repo_fetch_url, package)}',
                hostname=hostname,
            )
            if result.status != 0:
                raise CLIReturnCodeError(
                    result.status,
                    result.stderr,
                    f'Unable to download package {package}',
                )
    if wipe_repodata:
        result = ssh.command(f'rm -rf {repo_path}/repodata/', hostname=hostname)
        if result.status != 0:
            raise CLIReturnCodeError(
                result.status, result.stderr, 'Unable to delete repodata folder'
            )
    result = ssh.command(f'createrepo {repo_path}', hostname=hostname)
    if result.status != 0:
        raise CLIReturnCodeError(
            result.status,
            result.stderr,
            f'Unable to create repository. stderr contains following info:\n{result.stderr}',
        )

    published_url = 'http://{}{}/pulp/repos/{}/'.format(
        settings.server.hostname,
        f':{settings.server.port}' if settings.server.port else '',
        name,
    )

    return published_url


def repo_add_updateinfo(name, updateinfo_url=None, hostname=None):
    """Modify repo with contents of updateinfo.xml file.

    :param str name: repository name
    :param str optional updateinfo_url: URL to download updateinfo.xml file
        from. If not specified - updateinfo.xml from repository folder will be
        used instead
    :param str optional hostname: hostname or IP address of the remote host. If
        ``None`` the hostname will be get from ``main.server.hostname`` config.
    :return: result of executing `modifyrepo` command
    """
    updatefile = 'updateinfo.xml'
    repo_path = f'{PULP_PUBLISHED_YUM_REPOS_PATH}/{name}'
    updatefile_path = f'{repo_path}/{updatefile}'
    if updateinfo_url:
        result = ssh.command(f'find {updatefile_path}', hostname=hostname)
        if result.status == 0 and updatefile in result.stdout:
            result = ssh.command(
                f'mv -f {updatefile_path} {updatefile_path}.bak', hostname=hostname
            )
            if result.status != 0:
                raise CLIReturnCodeError(
                    result.status,
                    result.stderr,
                    f'Unable to backup existing {updatefile}',
                )
        result = ssh.command(f'wget -O {updatefile_path} {updateinfo_url}', hostname=hostname)
        if result.status != 0:
            raise CLIReturnCodeError(
                result.status, result.stderr, f'Unable to download {updateinfo_url}'
            )

    result = ssh.command(f'modifyrepo {updatefile_path} {repo_path}/repodata/')

    return result


def extract_ui_token(input):
    """Extracts and returns the CSRF protection token from a given
    HTML string"""
    token = re.search('"token":"(.*?)"', input)
    if token is None:
        raise IndexError("the given string does not contain any authenticity token references")
    else:
        return token[1]


def get_web_session():
    """Logs in as admin user and returns the valid requests.Session object"""
    sat_session = requests.Session()
    url = f'https://{settings.server.hostname}'

    init_request = sat_session.get(url, verify=False)
    login_request = sat_session.post(
        f'{url}/users/login',
        data={
            'authenticity_token': extract_ui_token(init_request.text),
            'login[login]': settings.server.admin_username,
            'login[password]': settings.server.admin_password,
            'commit': 'Log In',
        },
        verify=False,
    )
    login_request.raise_for_status()
    if 'users/login' in login_request.history[0].headers.get('Location'):
        raise requests.HTTPError('Failed to authenticate using the given credentials')
    return sat_session


def host_provisioning_check(ip_addr):
    """Check the provisioned host status by pinging the ip of host and check
    to connect to ssh port

    :param ip_addr: IP address of the provisioned host
    :return: ssh command return code and stdout
    """
    result = ssh.command(
        f'for i in {{1..60}}; do ping -c1 {ip_addr} && exit 0; sleep 20; done; exit 1'
    )
    if result.status != 0:
        raise ProvisioningCheckError(f'Failed to ping virtual machine Error:{result.stdout}')


def slugify_component(string, keep_hyphens=True):
    """Make component name a slug

    Arguments:
        string {str} -- Component name e.g: ActivationKeys
        keep_hyphens {bool} -- Keep hyphens or replace with underscores

    Returns:
        str -- component slug e.g: activationkeys
    """
    string = string.replace(" and ", "&")
    if not keep_hyphens:
        string = string.replace('-', '_')
    return re.sub("[^-_a-zA-Z0-9]", "", string.lower())


# --- Issue based Pytest markers ---


def idgen(val):
    """
    The id generator function which will return string that will append to the parameterized
    test name
    """
    return '_parameter'


class InstallerCommand:
    """This class constructs, parses, updates and gets formatted installer commands"""

    def __init__(self, *args, command='satellite-installer', allow_dupes=False, **kwargs):
        """This allows multiple methods for InstallerClass creation

        InstallerCommand('f', 'verbose', command='satellite-installer', sat_host='my_sat')
        InstallerCommand(installer_args=['f', 'verbose'], sat_host='my_sat')
        InstallerCommand(installer_args=['f', 'verbose'], installer_opts={'sat_host': 'my_sat'})

        :param allow_dupes: Allow duplicate options, doesn't apply to future updates

        """

        self.command = command
        self.args = kwargs.pop('installer_args', [])
        self.opts = kwargs.pop('installer_opts', {})
        self.update(*args, allow_dupes=allow_dupes, **kwargs)

    def get_command(self):
        """Construct the final command in the form of a string"""
        command_str = self.command
        for arg in self.args:
            command_str += f' {"-" if len(arg) == 1 else "--"}{arg}'
        for key, val in self.opts.items():
            # if we have duplicate keys (list of values), add each option/value pair
            if isinstance(val, list):
                for v in val:
                    command_str += f' --{key.replace("_", "-")} {v}'
            else:
                command_str += f' --{key.replace("_", "-")} {val}'
        return command_str

    def update(self, *args, allow_dupes=False, **kwargs):
        """Update one or more arguments and options
        values passed as positional and keyword arguments
        """
        new_args = [arg for arg in args if arg not in self.args]
        self.args.extend(new_args)
        if not allow_dupes:
            self.opts.update(kwargs)
        # iterate over all keyword arguments passed in
        for key, val in kwargs.items():
            # if we won't want duplicate keys, override the current value
            if not allow_dupes:
                self.opts[key] = val
            # if we do want duplicate keys, convert the value to a list
            elif curr_val := self.opts.get(key):  # noqa: E203
                val = [val]
                if not isinstance(curr_val, list):
                    curr_val = [curr_val]
                # and add the old value(s) to the new list
                val += curr_val
            self.opts[key] = val

    @classmethod
    def from_cmd_str(cls, command='satellite-installer', cmd_str=None):
        """Construct the class based on a string representing expected installer options.
        This is mostly used for capsule-certs-generate output parsing.
        """
        installer_command, listening = '', False
        for line in cmd_str.splitlines():
            if line.strip().startswith(command):
                listening = True
            if listening:
                installer_command += ' ' + ' '.join(line.replace('\\', '').split())
        installer_command = installer_command.replace(command, '').strip()
        cmd_args, add_later = {}, []
        for opt in installer_command.split('--'):
            if opt := opt.strip().split():  # noqa: E203
                if opt[0] in cmd_args:
                    add_later.append(opt)
                else:
                    cmd_args[opt[0]] = opt[1]
        installer = cls(command=command, installer_opts=cmd_args)
        for opt in add_later:
            installer.update(allow_dupes=True, **{opt[0]: opt[1]})
        return installer

    def __repr__(self):
        """Custom repr will give the constructed command output"""
        return self.get_command()
