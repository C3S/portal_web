# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

"""
Configuration settings for tests.
"""

testconfig = {
    'server': {
        # print debug messages to stdout (use nosetests -s to display)
        'debug': True,
        # settings for all services overriding the environment settings
        'settings': {},
        # gui configuration
        'gui': {
            # host for StopableWSGIServer
            'host': '0.0.0.0',
            # port for StopableWSGIServer
            'port': 6544,
            # environment file without '.ini'
            'environment': "testing",
            # individual settings for gui
            'settings': {},
        },
        # api configuration
        'api': {
            # host for StopableWSGIServer
            'host': '0.0.0.0',
            # port for StopableWSGIServer
            'port': 6545,
            # environment file without '.ini'
            'environment': "testing",
            # individual settings for api
            'settings': {},
        },
    },
    'client': {
        # connection
        'connection': {
            'selenium': 'http://test_browser:4444/wd/hub',
            'server': 'test_web',
            'keep_alive': True,
        },
        # desired_capabilities
        'desired_capabilities': {
            'acceptInsecureCerts': True,
            'browserName': 'firefox',
            'loggingPrefs': {'browser': 'ALL'}
        },
        # window size of client
        'window_size': {
            'width': 800,
            'height': 600
        },
        # take screenshots during integration tests
        'screenshots': {
            # switch all screnshots on or off
            'on': True,
            # path of screenshots
            'path': '/shared/tests/screenshots',
            # delete all screenshots of previous integration tests
            'reset': True
        }
    }
}
