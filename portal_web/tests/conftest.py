# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Pytest Fixtures
"""

import os
import subprocess
import glob
import datetime
import inspect
import logging
import pytest

from trytond.transaction import Transaction
from pyramid import testing
from paste.deploy.loadwsgi import appconfig
from webtest import TestApp
from webtest.http import StopableWSGIServer
from selenium.webdriver import Remote, FirefoxOptions

from portal_web import main
from portal_web.models import Tdb
from portal_web.config import get_plugins, replace_environment_vars


# --- pytest ------------------------------------------------------------------

def pytest_collection_modifyitems(session, config, items):
    """
    Fixes the nodid path string to show the full path.
    """
    # hack for vs code test explorer python adapter
    if int(os.environ.get("DEBUGGER_DEBUGPY", 0)) == 1:
        for item in items:
            relpath = os.path.relpath(item.path, "/shared/src")
            nodeid = "::".join([relpath] + item.nodeid.split("::")[1:])
            item._nodeid = f"{nodeid}"
        return items
    # use absolute paths for nodeids
    for item in items:
        nodeid = "::".join(
            [f"{item.path}"] + item.nodeid.split("::")[1:])
        item._nodeid = f"{nodeid}"
    return items


@pytest.fixture
def debug(caplog):
    caplog.set_level(logging.DEBUG, logger="pyramid")
    caplog.set_level(logging.DEBUG, logger="portal_web")
    caplog.set_level(logging.DEBUG, logger="collecting_society_web")


# --- database ----------------------------------------------------------------

@pytest.fixture(autouse=True, scope='session')
def reset_database():
    """
    Resets the database for each test run.
    """
    if os.environ.get('COMPOSE_PROJECT_NAME'):
        if int(os.environ.get('DB_KEEP', 0)) == 1:
            return
        subprocess.call(
            [
                'db-setup',
                'collecting_society_test_template',
                '--dataset', 'production',
                '--no-template',
            ]
        )
        subprocess.call(
            [
                'db-copy',
                '--force',
                'collecting_society_test_template',
                'collecting_society_test',
            ]
        )


# --- tryton ------------------------------------------------------------------

class TrytonHelper:
    """
    Tryton helper for use in pytests.

    Attributes:
        settings (paste.deploy.config): parsed pyramid ini config
        Tdb (Tdb): Tdb class
        pool (Pool): Initialized pool

    Methods:
        transaction: Tdb transaction decorator
        delete_records: helper function to delete records in reversed order
    """
    def __init__(self, settings):
        Tdb._db = settings['tryton.database']
        Tdb._company = settings['tryton.company']
        Tdb._user = settings['tryton.user']
        Tdb._configfile = settings['tryton.configfile']
        Tdb.init()

        self.settings = settings
        self.Tdb = Tdb
        self.pool = Tdb.pool()
        self.transaction = Tdb.transaction

    @staticmethod
    @Tdb.transaction(readonly=False)
    def delete_records(records):
        if not records:
            return
        records.reverse()
        for instance in records:
            instance.delete([instance])
        Transaction().commit()


@pytest.fixture(scope='session')
def tryton(settings):
    """
    Provides the tryton test helper class.

    Yields:
        TrytonHelper: Helper with usual tryton testing objects accessible
    """
    return TrytonHelper(settings)


# --- pyramid -----------------------------------------------------------------

@pytest.fixture(scope='session')
def settings():
    """
    Provides parsed pyramid settings (plugins combined, envvars substituted).
    """
    environment = 'testing'
    settings = appconfig(
        'config:' + os.path.join(
            os.path.dirname(__file__), '..', '..', f'{environment}.ini'
        )
    )
    plugins = get_plugins(settings, environment)
    for priority in sorted(plugins, reverse=True):
        settings.update(plugins[priority]['settings'])
    settings = replace_environment_vars(settings)
    return settings


class PyramidHelper:
    """
    Pyramid helper for use in pytests.

    Attributes:
        settings (paste.deploy.config): parsed pyramid ini config
        request (pyramid.testing.DummyRequest): empty dummy request
        resource (pyramid.testing.DummyResource): empty dummy resource
        config (pyramid.config.Configurator): pyramid app config
        registry (pyramid.registry.Registry): pyramid registry
    """
    def __init__(self, settings):
        self.settings = settings
        self.request = testing.DummyRequest()
        self.resource = testing.DummyResource()
        self.config = testing.setUp(request=self.request, settings=settings)
        self.registry = self.config.registry


@pytest.fixture
def pyramid(settings):
    """
    Provides the pyramid helper class.

    Yields:
        PyramidHelper: Helper with usual pyramid testing objects accessible
    """
    yield PyramidHelper(settings)
    testing.tearDown()


@pytest.fixture
def dummy_request():
    """
    Creates an empty dummy request.

    Returns:
        pyramid.testing.DummyRequest: dummy request
    """
    return testing.DummyRequest()


@pytest.fixture
def request_with_registry(settings):
    """
    Creates a request with registry set up.

    Returns:
        pyramid.testing.DummyRequest: dummy request
    """
    request = testing.DummyRequest()
    testing.setUp(request=request, settings=settings)
    return request


@pytest.fixture
def dummy_resource():
    """
    Creates an empty dummy resource.

    Returns:
        pyramid.testing.DummyResource: dummy resource
    """
    return testing.DummyResource()


# --- webtest -----------------------------------------------------------------

@pytest.fixture(scope='class')
def api(settings):
    """
    Sets up an webapi service with TestApp.

    Returns:
        webtest.TestApp: for functional tests with webtest
    """
    settings['service'] = "webapi"
    return TestApp(main({}, **settings))


@pytest.fixture(scope='class')
def gui(settings):
    """
    Sets up a webgui service with TestApp.

    Returns:
        webtest.TestApp: for functional tests with webtest
    """
    settings['service'] = "webgui"
    return TestApp(main({}, **settings))


# --- webdriver ---------------------------------------------------------------

@pytest.fixture(scope='session')
def browser_api(settings):
    """
    Sets up an webapi service with StopableWSGIServer.

    Yields:
        webtest.http.StopableWSGIServer: for integration tests with selenium
    """
    settings['service'] = "webapi"
    app = main({}, **settings)
    server = StopableWSGIServer.create(
        app, host='0.0.0.0', port=6545,
        clear_untrusted_proxy_headers=True, threads=10
    )
    if not server.wait():
        raise Exception('Server could not be fired up. Exiting ...')
    yield server
    server.shutdown()


@pytest.fixture(scope='session')
@pytest.mark.usefixtures('browser_api')
def browser_gui(settings):
    """
    Sets up a webgui service with StopableWSGIServer.

    Yields:
        webtest.http.StopableWSGIServer: for integration tests with selenium
    """
    settings['service'] = "webgui"
    app = main({}, **settings)
    server = StopableWSGIServer.create(
        app, host='0.0.0.0', port=6544,
        clear_untrusted_proxy_headers=True, threads=10
    )
    if not server.wait():
        raise Exception('Server could not be fired up. Exiting ...')
    yield server
    server.shutdown()


class BrowserHelper:
    """
    Browser helper for use in selenium tests with pytest.

    Notes:
    - undefined attributes of this class will be requested from self.browser
    - urls starting with "/" or "gui/" will send requests to the the webgui
      service and "api/" to the webapi service.

    Attributes:
        browser (webdriver.Remote): remote webdriver
        options (webdriver.Options): options used for the webdriver
        host (str): hostname/ip to remote access the app
        gui (webtest.http.StopableWSGIServer): webgui app
        api (webtest.http.StopableWSGIServer): webapi app
        screenshots (bool): create screenshots during a test run
        screenshot_path (str): directory for screenshots

    Methods:
        get: overrides browser.get to autocomplete the url and automate
    """
    def __init__(self, gui, api, screenshots=True,
                 screenshot_path='/shared/tests/screenshots'):
        # webdriver
        options = FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument('--verbose')
        options.set_capability('loggingPrefs', {'browser': 'ALL'})
        browser = Remote(
            command_executor='http://test_browser:4444/wd/hub',
            options=options
        )
        self.browser = browser
        self.options = options
        self.host = 'test_web'
        self.gui = gui
        self.api = api

        # window
        self.testsizes = {
            'xs': (360, 640),
            'sm': (768, 1024),
            'md': (1024, 768),
            'lg': (1920, 1080),
        }
        browser.set_window_size(*self.testsizes['lg'])

        # screenshots
        self.screenshots = screenshots
        self.screenshot_path = screenshot_path

    def __getattr__(self, name):
        """
        Delegate attribute access to browser.
        """
        return getattr(self.browser, name)

    def get(self, url, *args, **kwargs):
        """
        Overrides browser.get to autocomplete the url and automate screenshot
        handling. urls starting with "/" or "gui/" will send requests to the
        the webgui service and "api/" to the webapi service.
        """
        # get
        full_url = url
        if url.startswith(("/", "gui/")):
            full_url = f"http://{self.host}:{self.gui.addr[1]}/{url}"
        elif url.startswith("api/"):
            full_url = f"http://{self.host}:{self.api.addr[1]}/{url}"
        self.browser.get(full_url, *args, **kwargs)
        # screenshot
        url = f"GET-{url}".replace("/", "⧸").replace("?", "-QUERY-")
        self.screenshot("%s" % url)

    def screenshot(self, name=""):
        """
        Takes a screenshot of the current browser client viewport.
        """
        if not self.screenshots:
            return
        # generate filename
        testtime = datetime.datetime.utcnow().strftime('%y%m%d.%H%M%S.%f')[:-4]
        testclass = ''
        testmethod = ''
        for frameinfo in inspect.stack():
            if frameinfo[3].startswith('test_'):
                testclass = frameinfo[0].f_locals["self"].__class__.__name__
                testmethod = frameinfo[3]
        filename = f"{testtime}-{testclass}.{testmethod}-{name}".strip("._-")
        # make a screenshot for each screen resolution
        for name, size in self.testsizes.items():
            # resize window
            self.set_window_size(*size)
            required_height = self.execute_script(
                'return document.body.parentNode.scrollHeight')
            self.set_window_size(size[0], required_height)
            # make screenshot
            self.get_screenshot_as_file(os.path.join(
                self.screenshot_path, f'{name}-{filename}.png'))
        self.set_window_size(*self.testsizes['lg'])


screenshot_path = '/shared/tests/screenshots'


@pytest.fixture(autouse=True, scope='session')
def delete_screenshots():
    """
    Deletes all screenshots of previous selenium tests.
    """
    if not os.path.isdir(screenshot_path):
        os.makedirs(screenshot_path)
    path = os.path.join(screenshot_path, '*.png')
    for screenshot in glob.glob(path):
        os.unlink(screenshot)


@pytest.fixture(scope='session')
def browser(browser_gui, browser_api):
    """
    Provides the selenoum test browser.

    Yields:
        BrowserHelper: selenium remote connection to selenium hub service with
            additional helper functions
    """
    try:
        browser = BrowserHelper(
            gui=browser_gui, api=browser_api,
            screenshots=True, screenshot_path=screenshot_path)
        yield browser
    finally:
        browser.quit()


@pytest.fixture
def reset(request):
    """
    Resets the session.
    """
    if 'gui' in request.fixturenames:
        gui = request.getfixturevalue('gui')
        if isinstance(gui, TestApp):
            gui.reset()
    if 'api' in request.fixturenames:
        api = request.getfixturevalue('gui')
        if isinstance(api, TestApp):
            api.reset()
    if 'browser' in request.fixturenames:
        browser = request.getfixturevalue('browser')
        browser.delete_all_cookies()
        browser.refresh()
        browser.set_window_size(*browser.testsizes['lg'])


# --- models ------------------------------------------------------------------

@pytest.fixture(scope='class')
def create_party(tryton):
    """
    Yields a function to create a party.
    """
    records = []
    Party = tryton.pool.get('party.party')

    @staticmethod
    @tryton.transaction(readonly=False)
    def create(**kwargs):
        party = Party(**kwargs)
        party.save()
        records.append(party)
        return party

    yield create

    tryton.delete_records(records)


@pytest.fixture(scope='class')
def create_web_user(tryton):
    """
    Yields a function to create a web user.
    """
    records = []
    WebUser = tryton.pool.get('web.user')
    WebUserRole = tryton.pool.get('web.user.role')

    @staticmethod
    @tryton.transaction(readonly=False)
    def create(**kwargs):
        if 'roles' not in kwargs:
            kwargs['roles'] = WebUserRole.search([])
        web_user = WebUser(**kwargs)
        web_user.save()
        records.append(web_user)
        return web_user

    yield create

    tryton.delete_records(records)
