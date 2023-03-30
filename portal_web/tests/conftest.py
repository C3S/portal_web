# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Pytest Fixtures
"""

import os
import glob
import datetime
import inspect
import pytest

from trytond.transaction import Transaction
from pyramid import testing
from paste.deploy.loadwsgi import appconfig
from webtest import TestApp
from webtest.http import StopableWSGIServer
from selenium.webdriver import Remote, FirefoxOptions

from .. import main
from ..models import Tdb
from ..config import get_plugins, replace_environment_vars

__ALL__ = [
    'tryton',

    'settings',
    'pryamid',

    'gui',
    'api',
    'browser',
    'reset',

    'create_party',
    'create_web_user',
]


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


@pytest.fixture(scope='module')
def tryton(settings):
    """
    Provides the tryton test helper class.
    """
    return TrytonHelper(settings)


# --- pyramid -----------------------------------------------------------------

@pytest.fixture(scope='module')
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
    """
    return PyramidHelper(settings)


# --- app ---------------------------------------------------------------------

@pytest.fixture(scope='module')
def gui(request, settings):
    """
    Sets up a webgui service.

    Yields:
        webtest.http.StopableWSGIServer: if path matches */integration/*,
            for integration tests with webdriver/selenium
        webtest.TestApp: otherwise, for functional tests with webtest
    """
    settings['service'] = "webgui"
    app = main({}, **settings)
    # StopableWSGIServer for integration tests with webdriver/selenium
    if request.path.match('*/integration/*'):
        request.getfixturevalue('api')
        server = StopableWSGIServer.create(
            app, host='0.0.0.0', port=6544,
            clear_untrusted_proxy_headers=True, threads=10
        )
        if not server.wait():
            raise Exception('Server could not be fired up. Exiting ...')
        yield server
        server.shutdown()
    # TestApp for functional tests with webtest
    else:
        yield TestApp(main({}, **settings))


@pytest.fixture(scope='module')
def api(request, settings):
    """
    Sets up an webapi service.

    Yields:
        webtest.http.StopableWSGIServer: if path matches */integration/*,
            for integration tests with webdriver/selenium
        webtest.TestApp: otherwise, for functional tests with webtest
    """
    settings['service'] = "webapi"
    app = main({}, **settings)
    # StopableWSGIServer for integration tests with webdriver/selenium
    if request.path.match('*/integration/*'):
        server = StopableWSGIServer.create(
            app, host='0.0.0.0', port=6545,
            clear_untrusted_proxy_headers=True, threads=10
        )
        if not server.wait():
            raise Exception('Server could not be fired up. Exiting ...')
        yield server
        server.shutdown()
    # TestApp for functional tests with webtest
    else:
        yield TestApp(app)


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
        gui (str): url for the webgui
        api (str): url for the webapi
        screenshots (bool): create screenshots during a test run
        screenshot_path (str): directory for screenshots
        screenshot_delete (bool): delete screenshots before each test run

    Methods:
        get: overrides browser.get to autocomplete the url and automate
    """
    def __init__(self, screenshots=True, screenshot_delete=True):
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
        self.gui = 'http://test_web:6544'
        self.api = 'http://test_web:6545'

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
        self.screenshot_path = '/shared/tests/screenshots'
        self.screenshot_delete = screenshot_delete
        if screenshot_delete:
            self.delete_screenshots()

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
        if url.startswith(("/", "gui/")):
            url = f"{self.gui}{url}"
        elif url.startswith("api/"):
            url = f"{self.api}{url}"
        self.browser.get(url, *args, **kwargs)

    def screenshot(self, name=""):
        """
        Takes a screenshot of the current browser client viewport.
        """
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

    def delete_screenshots(self):
        """
        Deletes all screenshots of previous selenium tests.
        """
        if not os.path.isdir(self.screenshot_path):
            os.makedirs(self.screenshot_path)
        path = os.path.join(self.screenshot_path, '*.png')
        for screenshot in glob.glob(path):
            os.unlink(screenshot)


@pytest.fixture(scope='module')
def browser(gui, api):
    """
    Provides the test browser.
    """
    try:
        browser = BrowserHelper()
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
        browser.delete_all_cookies()
        browser.set_window_size(*browser.testsizes['lg'])


# --- models ------------------------------------------------------------------

@pytest.fixture(scope='class')
def create_party(tryton):
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
