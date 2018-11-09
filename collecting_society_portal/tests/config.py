# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

"""
Configuration settings for tests.
"""

testconfig = {
    'server': {
        # host for StopableWSGIServer
        'host': '0.0.0.0',
        # port for StopableWSGIServer
        'port': '6544',
        # environment file without '.ini'
        'environment': "testing",
        # settings overriding the environment settings
        'settings': {},
        # print debug messages to stdout (use nosetests -s to display)
        'debug': True
    },
    'client': {
        # connection
        'connection': {
            'selenium': 'http://selenium:4444/wd/hub',
            'server': 'portal:6544'
        },
        # desired_capabilities
        'desired_capabilities': {
            'browserName': 'firefox',
            'acceptInsecureCerts': True,
            'marionette': True
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
            'path': '/ado/tmp/screenshots',
            # delete all screenshots of previous integration tests
            'reset': True
        }
    }
}
