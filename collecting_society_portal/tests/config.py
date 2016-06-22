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
        # desired_capabilities
        'desired_capabilities': {
            'platform': 'ANY',
            'browserName': 'phantomjs',
            'version': '',
            'javascriptEnabled': True
        },
        # window size of client
        'window_size': {
            'width': 1600,
            'height': 768
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
