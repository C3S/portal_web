# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import os
from datetime import datetime
from functools import wraps

import unittest
from webtest import TestApp
from webtest.http import StopableWSGIServer
from selenium import webdriver
from paste.deploy.loadwsgi import appconfig
from pyramid import testing

from ..models import Tdb
from ..config import get_plugins
from .. import main
from .config import testconfig

from .integration.pageobjects import *


class Net(object):

    _instance = None

    # singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Net, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def start_server(self, settings={}, wrapper='StopableWSGIServer'):
        # appconfig
        self.appconfig = appconfig(
            'config:' + os.path.join(
                os.path.dirname(__file__), '..', '..',
                testconfig['server']['environment'] + '.ini'
            )
        )
        self.appconfig.update(testconfig['server']['settings'])
        self.appconfig.update(settings)
        self.plugins = get_plugins(self.appconfig)
        # app
        app = main({}, **self.appconfig)
        if wrapper == 'StopableWSGIServer':
            self.srv = StopableWSGIServer.create(
                app,
                host=testconfig['server']['host'],
                port=testconfig['server']['port']
            )
            if not self.srv.wait():
                raise Exception('Server could not be fired up. Exiting ...')
        elif wrapper == 'TestApp':
            self.srv = TestApp(app)
        else:
            raise Exception('Wrapper could not be found. Exiting ...')
        return self.srv

    def stop_server(self):
        if isinstance(self.srv, StopableWSGIServer):
            self.srv.shutdown()

    def start_client(self):
        self.cli = webdriver.PhantomJS(
            desired_capabilities=testconfig['client']['desired_capabilities']
        )
        self.cli.set_window_size(
            testconfig['client']['window_size']['width'],
            testconfig['client']['window_size']['height']
        )
        return self.cli

    def stop_client(self):
        self.cli.quit()


class TestBase(unittest.TestCase):

    cfg = testconfig
    net = Net()

    def __init__(self, methodName='runTest'):
        super(TestBase, self).__init__(methodName)
        self._shortDescription = self.shortDescription
        self.shortDescription = self.customShortDescription

    # overload: configuration of individual appsettings for test class
    @classmethod
    def settings(cls):
        return {}

    def customShortDescription(self):
        typ = self.__module__.split('.')[2].capitalize()
        if typ == "Unit":
            typ += " | " + self.__module__.split('.')[3].capitalize()
        plugin = self.__module__.split('.')[0].split('_')[-1].capitalize()
        classname = self.__class__.__name__[4:].capitalize()
        return plugin + " | " + typ + " | " + classname + " | " +\
            self._shortDescription()

    def debug(self, msg=''):
        if self.cfg['server']['debug']:
            line = '-'*30
            print(
                "\n\n" + line + " DEBUG START " + line + "\n\n" +
                msg +
                "\n\n" + line + "  DEBUG END  " + line + "\n"
            )


class UnitTestBase(TestBase):

    @classmethod
    def setUpClass(cls):
        cls.config = testing.setUp()

    @classmethod
    def tearDownClass(cls):
        testing.tearDown()


class FunctionalTestBase(TestBase):

    @classmethod
    def setUpClass(cls):
        cls.srv = cls.net.start_server(
            settings=cls.settings(),
            wrapper='TestApp'
        )

    @classmethod
    def tearDownClass(cls):
        cls.net.stop_server()

    def session(self):
        '''starts a new session'''
        self.srv.reset()

    def url(self, url='', **kwargs):
        return self.srv.get('/' + url, **kwargs)


class IntegrationTestBase(TestBase):

    @classmethod
    def setUpClass(cls):
        cls.cli = cls.net.start_client()
        cls.srv = cls.net.start_server(
            settings=cls.settings(),
            wrapper='StopableWSGIServer'
        )

    @classmethod
    def tearDownClass(cls):
        cls.net.stop_client()
        cls.net.stop_server()

    def url(self, url=''):
        self.cli.get(
            'http://' +
            self.cfg['server']['host'] + ':' +
            self.cfg['server']['port'] + '/' +
            url
        )

    def session(self):
        '''starts a new session'''
        self.cli.start_session(self.cfg['client']['desired_capabilities'])
        self.cli.set_window_size(
            self.cfg['client']['window_size']['width'],
            self.cfg['client']['window_size']['height']
        )

    def screenshot(self, filename=''):
        if self.cfg['client']['screenshots']['on']:
            path = self.cfg['client']['screenshots']['path']
            if not os.path.isdir(path):
                os.makedirs(path)
            if filename is '':
                testtime = datetime.utcnow().strftime('%Y.%m.%d-%H:%M:%S.%f')
                testclass = self.__class__.__name__
                testname = self._testMethodName
                filename = testtime + "-" + testclass + "-" + testname
            self.cli.get_screenshot_as_file(
                os.path.join(path, filename + '.png')
            )
