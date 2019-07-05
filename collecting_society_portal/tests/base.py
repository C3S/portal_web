# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

"""
Base classes for tests.

Test classes should extend one of the base classes:

- UnitTestBase (unit tests with unittest)
- FunctionalTestBase (functional tests with webtest)
- IntegrationTestBase (integration tests with webdriver)
"""

import os
from datetime import datetime

import unittest
from webtest import TestApp
from webtest.http import StopableWSGIServer
from selenium import webdriver
from paste.deploy.loadwsgi import appconfig
from pyramid import testing

from ..config import (
    get_plugins,
    replace_environment_vars
)
from .. import main
from .config import testconfig

from .integration.pageobjects import *  # noqa

from ..models import Tdb
from trytond.transaction import Transaction
from trytond.cache import Cache
from trytond.pool import Pool


class Net(object):
    """
    Net containing server/client objects used in tests.

    Includes functions to start and stop the server/client.

    Note:
        This class uses the singleton pattern.

    Classattributes:
        _instance (Net): First instance of this class (singleton) or None.

    Attributes:
        srv (webtest.http.StopableWSGIServer||webtest.TestApp): Server object.
        cli (selenium.webdriver.PhantomJS): Client object.
        appconfig (dict): Parsed [app:main] section of .ini file.
        plugins (dict): Plugin configuration.
    """
    _instance = None

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

    def start_server(self, settings={}, wrapper='StopableWSGIServer'):
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
            settings (dict): Custom server settings
            wrapper (Optional[str]): StopableWSGIServer||TestApp

        Returns:
            webtest.http.StopableWSGIServer: If StopableWSGIServer.
            webtest.TestApp: If TestApp.
        """

        # Appconfig
        self.appconfig = appconfig(
            'config:' + os.path.join(
                os.path.dirname(__file__), '..', '..',
                testconfig['server']['environment'] + '.ini'
            )
        )
        self.appconfig.update(testconfig['server']['settings'])
        self.appconfig.update(settings)

        # Plugins
        self.plugins = get_plugins(self.appconfig)

        # update portal settings with plugin settings and replace env vars
        for priority in sorted(self.plugins, reverse=True):
            self.appconfig.update(self.plugins[priority]['settings'])

        # Evironment
        self.appconfig = replace_environment_vars(self.appconfig)

        # App
        app = main({}, **self.appconfig)

        # StopableWSGIServer
        if wrapper == 'StopableWSGIServer':
            self.srv = StopableWSGIServer.create(
                app,
                host=testconfig['server']['host'],
                port=testconfig['server']['port']
            )
            if not self.srv.wait():
                raise Exception('Server could not be fired up. Exiting ...')

        # TestApp
        elif wrapper == 'TestApp':
            self.srv = TestApp(app)

        # Not implemented
        else:
            raise Exception('Wrapper could not be found. Exiting ...')

        return self.srv

    def stop_server(self):
        """
        Stops the server.

        Returns:
            None.
        """
        if isinstance(self.srv, StopableWSGIServer):
            self.srv.shutdown()

    def start_client(self):
        """
        Starts the client.

        Only relevant for Selenium.
        Client settings may be configured in `config.py` (client).

        Returns:
            selenium.webdriver.PhantomJs: PhantomJs client.
        """
        # self.cli = webdriver.PhantomJS(
        #     desired_capabilities=testconfig['client']['desired_capabilities']
        # )
        self.cli = webdriver.Remote(
            command_executor=testconfig['client']['connection']['selenium'],
            desired_capabilities=testconfig['client']['desired_capabilities']
        )
        # self.cli.set_window_size(
        #     testconfig['client']['window_size']['width'],
        #     testconfig['client']['window_size']['height']
        # )
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
    """
    cfg = testconfig
    net = Net()

    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(*args, **kwargs)
        self._shortDescription = self.shortDescription
        self.shortDescription = self.prettyShortDescription

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

        Sets up pyramid registry and request for testing.

        Returns:
            None.
        """
        cls.config = testing.setUp()

    @classmethod
    def tearDownClass(cls):
        """
        Tears down test class.

        Tears down pyramid registry and request for testing.

        Returns:
            None.
        """

        testing.tearDown()


class FunctionalTestBase(TestBase):
    """
    Base class for functional tests (webtest).

    Classattributes:
        srv (webtest.TestApp||None): Server.
    """
    srv = None

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

        Starts TestApp server injecting the class app settings.

        Returns:
            None.
        """
        cls.srv = cls.net.start_server(
            settings=cls.settings(),
            wrapper='TestApp'
        )

        user = Transaction().user  # pyramid subrequests have no cursor
        cursor = Transaction().cursor and not Transaction().cursor._conn.closed
        if not user and not cursor:
            with Transaction().start(Tdb._db, 0):
                pool = Pool(str(Tdb._db))
                user = pool.get('res.user')
                context = user.get_preferences(context_only=True)
                Cache.clean(Tdb._db)
            Transaction().start(
                Tdb._db, Tdb._user, readonly=True, context=context)

    @classmethod
    def tearDownClass(cls):
        """
        Tears down test class.

        Stops TestApp server.

        Returns:
            None.
        """

        cursor = Transaction().cursor
        if cursor and not Transaction().cursor._conn.closed:
            Cache.resets(Tdb._db)
            Transaction().stop()

        cls.net.stop_server()

    def session(self):
        """
        Starts a new session.

        Returns:
            None.
        """
        self.srv.reset()

    def url(self, url='', **kwargs):
        """
        Requests an url from the TestApp.

        Returns:
            webtest.TestApp: TestApp resource.
        """
        return self.srv.get('/' + url, **kwargs)


class IntegrationTestBase(TestBase):
    """
    Base class for integration tests (webdriver).

    Classattributes:
        srv (webtest.http.StopableWSGIServer||None): Server.
        cli (selenium.webdriver.PhantomJS||None): Client.
    """
    srv = None
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
        Starts PhantomJs Client.

        Returns:
            None.
        """
        cls.cli = cls.net.start_client()
        cls.srv = cls.net.start_server(
            settings=cls.settings(),
            wrapper='StopableWSGIServer'
        )

    @classmethod
    def tearDownClass(cls):
        """
        Tears down test class.

        Stops StopableWSGIServer server.
        Stops PhantomJs client.

        Returns:
            None.
        """
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

    def url(self, url=''):
        """
        Requests an url from the StopableWSGIServer.

        Returns:
            None.
        """
        self.cli.get(
            'http://' + self.cfg['client']['connection']['server'] + '/' + url
        )

    def screenshot(self, filename=''):
        """
        Takes a screenshot of the current PhantomJs client viewport.

        Screenshots may be switched on/off in `config.py`
        (client/screenshots/on).

        The path in which the screenshots will be saved is configured in
        `config.py` (client/screenshots/path). The directory will be created,
        if it not exists.

        If no filename given it will be a concatenation of:

        - time of execution
        - test classname
        - test method

        Args:
            filename (Optional[str]): Screenshot filename without extension.
        """
        if self.cfg['client']['screenshots']['on']:
            path = self.cfg['client']['screenshots']['path']
            if not os.path.isdir(path):
                os.makedirs(path)
            if filename == '':
                testtime = datetime.utcnow().strftime('%Y.%m.%d-%H:%M:%S.%f')
                testclass = self.__class__.__name__
                testname = self._testMethodName
                filename = testtime + "-" + testclass + "-" + testname
            self.cli.get_screenshot_as_file(
                os.path.join(path, filename + '.png')
            )
