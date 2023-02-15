# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Base classes for tests.

Test classes should extend one of the base classes:

- UnitTestBase (unit tests with unittest)
- FunctionalTestBase (functional tests with webtest)
- IntegrationTestBase (integration tests with webdriver)
"""

import os
import re
import unicodedata
from datetime import datetime
import warnings

import unittest
from webtest import TestApp
from webtest.http import StopableWSGIServer
from selenium import webdriver
from paste.deploy.loadwsgi import appconfig

from pyramid import testing
from trytond.transaction import Transaction

from ..models import Tdb
from ..config import (
    get_plugins,
    replace_environment_vars
)
from .. import main

from .config import testconfig
from .integration.pageobjects import *  # noqa

re_ascii = re.compile(r"[^A-Za-z0-9_.,-]")


class Net(object):
    """
    Net containing server/client objects used in tests.

    Includes functions to start and stop the server/client.

    Note:
        This class uses the singleton pattern.

    Classattributes:
        _instance (Net): First instance of this class (singleton) or None.

    Attributes:
        gui (webtest.http.StopableWSGIServer||webtest.TestApp): Gui server.
        api (webtest.http.StopableWSGIServer||webtest.TestApp): Api server.
        cli (selenium.webdriver.Remote): Client object.
        appconfig[service] (dict): Appconfig of service.
        plugins (dict): Plugin configuration.
    """
    _instance = None
    appconfig = {}

    def __new__(cls, *args, **kwargs):
        """
        Singeton Pattern.

        Args:
            args (tuple): positional arguments
            kwargs (dict): keyword arguments

        Returns:
            Net: First instance of this class (singleton) or None.
        """
        if not cls._instance:
            cls._instance = super(Net, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def start_server(self, service, settings={}, wrapper='StopableWSGIServer'):
        """
        Starts the server.

        Server settings may be configured in `config.py` (server).

        The server may be an instance of

        - TestApp for functional tests with webtest.
        - StopableWSGIServer for integration tests with selenium.

        All server types are configured by the same appconfig `.ini` defined in
        `config.py` (server/environment). These settings are overwritten with

        1. the settings defined in `config.py` (server/settings).
        2. the settings provided to this function as argument.

        Args:
            service (String): api|gui
            settings (dict): Custom server settings
            wrapper (Optional[str]): StopableWSGIServer||TestApp

        Returns:
            webtest.http.StopableWSGIServer: If StopableWSGIServer.
            webtest.TestApp: If TestApp.
        """
        # Sanity checks
        if service not in ['gui', 'api']:
            raise Exception('Service could not be found. Exiting ...')
        if Tdb.is_open():
            Transaction().stop()

        # Main settings for the app
        environment = testconfig['server'][service]['environment']
        _appconfig = appconfig(
            'config:' + os.path.join(
                os.path.dirname(__file__), '..', '..',
                environment + '.ini'
            )
        )

        # Main settings for the plugins
        self.plugins = get_plugins(_appconfig, environment)
        for priority in sorted(self.plugins, reverse=True):
            _appconfig.update(self.plugins[priority]['settings'])

        # Test settings for all services
        _appconfig.update(testconfig['server']['settings'])

        # Test settings for this service
        _appconfig.update(testconfig['server'][service]['settings'])

        # Test settings for this run
        _appconfig.update(settings)

        # Set service
        _appconfig['service'] = "web" + service

        # Environment
        _appconfig = replace_environment_vars(_appconfig)

        # App
        self.appconfig[service] = _appconfig
        app = main({}, **self.appconfig[service])

        # Filter Warnings
        warnings.filterwarnings(  # lost socket connections
            action="ignore", message="unclosed",
            category=ResourceWarning)
        warnings.filterwarnings(  # TODO: upstream bug in pyramid_chameleon
            action="ignore", message="Use of .. or absolute path",
            category=DeprecationWarning)
        warnings.filterwarnings(  # TODO: upgrade pyramid auth methods
            action="ignore", message="Authentication and authorization",
            category=DeprecationWarning)

        # StopableWSGIServer
        if wrapper == 'StopableWSGIServer':
            server = StopableWSGIServer.create(
                app,
                host=testconfig['server'][service]['host'],
                port=testconfig['server'][service]['port'],
                clear_untrusted_proxy_headers=True
            )
            if not server.wait():
                raise Exception('Server could not be fired up. Exiting ...')

        # TestApp
        elif wrapper == 'TestApp':
            server = TestApp(app)

        # Not implemented
        else:
            raise Exception('Wrapper could not be found. Exiting ...')

        setattr(self, service, server)
        return server

    def stop_server(self):
        """
        Stops the server.

        Returns:
            None.
        """
        # Stop any previous Transaction
        if Tdb.is_open():
            Transaction().stop()

        # Stop server
        if isinstance(self.api, StopableWSGIServer):
            self.api.shutdown()
        if isinstance(self.gui, StopableWSGIServer):
            self.gui.shutdown()

    def start_client(self):
        """
        Starts the client.

        Only relevant for Selenium.
        Client settings may be configured in `config.py` (client).

        Returns:
            selenium.webdriver.Remote: Remote client.
        """
        options = webdriver.FirefoxOptions()
        for key, value in testconfig['client']['capabilities'].items():
            options.set_capability(key, value)
        self.cli = webdriver.Remote(
            command_executor=testconfig['client']['connection']['selenium'],
            options=options
        )
        return self.cli

    def stop_client(self):
        """
        Stops the client.

        Returns:
            None.
        """
        self.cli.quit()


class TestBase(unittest.TestCase):
    """
    Base class for all tests.

    Adds pretty short test descriptions to print to stdout by overriding the
    method `shortDescription()`.

    Args:
        args (tuple): positional arguments
        kwargs (dict): keyword arguments

    Classattributes:
        cfg (dict): Test specific configuration for server/client.
        net (Net): Net containing server/client objects for tests.
        data (list[obj]): Created tryton test objects.
    """
    cfg = testconfig
    net = Net()
    data = []

    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        self._shortDescription = self.shortDescription
        self.shortDescription = self.prettyShortDescription

    @classmethod
    def setUpClass(cls):
        """
        Injects test data method and commits cursor.

        Returns:
            None.
        """
        if Tdb.is_open():
            Transaction().commit()

    @classmethod
    @Tdb.transaction(readonly=False)
    def tearDownClass(cls):
        """
        Deletes tryton test data.

        Returns:
            None.
        """
        # Delete tryton test objects
        if cls.data:
            cls.data.reverse()
            for instance in cls.data:
                instance.delete([instance])
            Transaction().commit()

    def prettyShortDescription(self):
        """
        Generates pretty short test descriptions.

        The description contains:

        - Portal or plugin name
        - Test type and path
        - Test class name
        - Test method name

        Note:
            Unit tests are expected to be in a subpath of `tests/unit`, e.g.
            `tests/unit/models` or `tests/unit/views`.

        Examples:
            Portal | Unit | Models | Tdb | Is pool a Pool object? ... ok
            Portal | Functional | Login | email has to be well formed ... ok
            Imp | Integration | Webuser | logout logs user out ... ok

        Returns:
            str: Custom descripton.
        """

        # Portal or plugin name
        plugin = self.__module__.split('.')[0].split('_')[-1].capitalize()

        # Test type and path
        typ = self.__module__.split('.')[2].capitalize()
        if typ == "Unit":
            typ += " | " + self.__module__.split('.')[3].capitalize()

        # Test class name
        classname = self.__class__.__name__[4:].capitalize()

        # Test method name
        methodname = self._shortDescription()

        return plugin + " | " + typ + " | " + classname + " | " + methodname

    def debug(self, msg=''):
        """
        Prints debug messages to stdout.

        The debug messages may be switched on/off in `config.py` (server/debug)
        and are wrapped by a line for the start/end of the debug message.

        Returns:
            None.
        """
        if self.cfg['server']['debug']:
            line = '-'*30
            print(
                "\n\n" + line + " DEBUG START " + line + "\n\n" +
                msg +
                "\n\n" + line + "  DEBUG END  " + line + "\n"
            )


class UnitTestBase(TestBase):
    """
    Base class for unit tests (unittest).
    """
    @classmethod
    def setUpClass(cls):
        """
        Sets up test class.

        Configures Tdb database parameters.
        Sets up pyramid registry and request for testing.

        Returns:
            None.
        """
        service = 'gui'
        cls.settings = appconfig(
            'config:' + os.path.join(
                os.path.dirname(__file__), '..', '..',
                testconfig['server'][service]['environment'] + '.ini'
            )
        )
        cls.settings.update(testconfig['server']['settings'])
        cls.settings.update(testconfig['server'][service]['settings'])
        cls.settings = replace_environment_vars(cls.settings)
        Tdb._db = cls.settings['tryton.database']
        Tdb._company = cls.settings['tryton.company']
        Tdb._user = cls.settings['tryton.user']
        Tdb._configfile = cls.settings['tryton.configfile']

        super(UnitTestBase, cls).setUpClass()

        cls.config = testing.setUp()

    @classmethod
    def tearDownClass(cls):
        """
        Tears down test class.

        Tears down pyramid registry and request for testing.

        Returns:
            None.
        """
        super(UnitTestBase, cls).tearDownClass()
        testing.tearDown()


class FunctionalTestBase(TestBase):
    """
    Base class for functional tests (webtest).

    Classattributes:
        gui (webtest.TestApp||None): Gui server.
        api (webtest.TestApp||None): Api server.
    """
    gui = None
    api = None

    @classmethod
    def settings(cls):
        """
        Custom app settings for the scope of a test class.

        Override this method, to provide custom app settings to a server
        running for all tests within a test class.

        Note:
            The settings are included in setUpClass().

        Returns:
            dict: App settings.
        """
        return {}

    @classmethod
    def setUpClass(cls):
        """
        Sets up test class.

        Starts TestApp server.

        Returns:
            None.
        """
        cls.gui = cls.net.start_server(
            'gui',
            settings=cls.settings(),
            wrapper='TestApp'
        )
        cls.api = cls.net.start_server(
            'api',
            settings=cls.settings(),
            wrapper='TestApp'
        )
        super(FunctionalTestBase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Tears down test class.

        Stops TestApp server.

        Returns:
            None.
        """
        super(FunctionalTestBase, cls).tearDownClass()
        cls.net.stop_server()

    def session(self):
        """
        Starts a new session.

        Returns:
            None.
        """
        self.gui.reset()
        self.api.reset()

    def url(self, service='gui', url='', **kwargs):
        """
        Requests an url from the TestApp.

        Returns:
            webtest.TestApp: TestApp resource.
        """
        return getattr(self, service).get(url, **kwargs)


class IntegrationTestBase(TestBase):
    """
    Base class for integration tests (webdriver).

    Classattributes:
        gui (webtest.http.StopableWSGIServer||None): Gui server.
        api (webtest.http.StopableWSGIServer||None): Api server.
        cli (selenium.webdriver.Remote||None): Client.
    """
    gui = None
    api = None
    cli = None

    @classmethod
    def settings(cls):
        """
        Custom app settings for the scope of a test class.

        Override this method, to provide custom app settings to a server
        running for all tests within a test class.

        Note:
            The settings are included in setUpClass().

        Returns:
            dict: App settings.
        """
        return {}

    @classmethod
    def setUpClass(cls):
        """
        Sets up test class.

        Starts StopableWSGIServer server injecting the class app settings.
        Starts Browser Client.

        Returns:
            None.
        """
        cls.gui = cls.net.start_server(
            'gui',
            settings=cls.settings(),
            wrapper='StopableWSGIServer'
        )
        cls.api = cls.net.start_server(
            'api',
            settings=cls.settings(),
            wrapper='StopableWSGIServer'
        )
        cls.cli = cls.net.start_client()
        super(IntegrationTestBase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Tears down test class.

        Stops StopableWSGIServer server.
        Stops Browser client.

        Returns:
            None.
        """
        super(IntegrationTestBase, cls).tearDownClass()
        cls.net.stop_client()
        cls.net.stop_server()

    def session(self):
        """
        Starts a new session.

        Returns:
            None.
        """
        self.cli.start_session(self.cfg['client']['desired_capabilities'])
        self.cli.set_window_size(
            self.cfg['client']['window_size']['width'],
            self.cfg['client']['window_size']['height']
        )

    def url(self, service='gui', url=''):
        """
        Requests an url from the StopableWSGIServer.

        Returns:
            None.
        """
        self.cli.get(
            'http://'
            + self.cfg['client']['connection']['server']
            + ":" + str(self.cfg['server'][service]['port'])
            + url
        )
        url = url.lstrip("/")
        url = url.replace("/", ",")
        if not url:
            url = "ROOT"
        self.screenshot("URL-%s" % url)

    def screenshot(self, name=''):
        """
        Takes a screenshot of the current browser client viewport.

        Screenshots may be switched on/off in `config.py`
        (client/screenshots/on).

        The path in which the screenshots will be saved is configured in
        `config.py` (client/screenshots/path). The directory will be created,
        if it not exists.

        The filename will be a concatenation of:

        - time of execution
        - test classname
        - test method
        - name if provided

        Args:
            filename (Optional[str]): Additional name postfix for the file.
        """
        if self.cfg['client']['screenshots']['on']:
            # create path
            path = self.cfg['client']['screenshots']['path']
            if not os.path.isdir(path):
                os.makedirs(path)
            # concat filename
            testtime = datetime.utcnow().strftime('%y%m%d.%H%M%S.%f')[:-4]
            testclass = self.__class__.__name__.removeprefix("Test")
            testmethod = [
                word.title() for word in
                self._testMethodName.removeprefix("test_").split('_')]
            if testmethod and testmethod[0].isnumeric():
                testmethod[0] += "-"
            testmethod = ''.join(testmethod)
            filename = [testtime, testclass, testmethod]
            if name:
                filename.append(name)
            filename = "-".join(filename)
            # sanitize filename (taken from werkzeug.utils.secure_filename)
            filename = unicodedata.normalize("NFKD", filename)
            filename = filename.encode("ascii", "ignore").decode("ascii")
            for sep in os.path.sep, os.path.altsep:
                if sep:
                    filename = filename.replace(sep, " ")
            filename = str(
                re_ascii.sub("", "_".join(filename.split()))
            ).strip("._-")
            # make screenshot
            self.cli.get_screenshot_as_file(
                os.path.join(path, filename + '.png')
            )
