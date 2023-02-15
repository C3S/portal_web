#!/usr/bin/env python
# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web
"""
Setup of egg including portal_web
"""

import os
from setuptools import setup, find_packages

MODULE = 'portal_web'
PREFIX = 'c3s'

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGELOG.rst')) as f:
    CHANGELOG = f.read()

service = str(os.environ.get('PYRAMID_SERVICE'))
environment = str(os.environ.get('ENVIRONMENT'))

install_requires = [
    'c3s_collecting_society',
    'colander',
    'cornice',
    'cornice_swagger',
    'cryptacular',
    'deform',
    'Pillow',
    'pyramid',
    'pyramid_beaker',
    'pyramid_chameleon',
    'pyramid_mailer',
    'python-magic',
    'trytond<6.7',
    'waitress',
]
if environment == "development":
    install_requires.append('pyramid_debugtoolbar')

test_requires = [
    'coverage',
    'nose',
    'webtest',
    'selenium',
]

setup(
    name='%s_%s' % (PREFIX, MODULE),
    version='0.2',
    description=(
        'Web Portal'
    ),
    long_description=README + '\n\n' + CHANGELOG,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Legal Industry',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Natural Language :: German',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Artistic Software',
    ],
    license='GPL-3',
    author='Alexander Blum',
    author_email='alexander.blum@c3s.cc',
    url='https://github.com/C3S/portal_web',
    keywords='web pyramid pylons collecting society',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=test_requires,
    test_suite='%s' % (MODULE),
    entry_points="""\
    [paste.app_factory]
    main = %s:main
    """ % (MODULE),
)
