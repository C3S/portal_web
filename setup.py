#!/usr/bin/env python
# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal
"""
Setup of egg including collecting_society_portal
"""

import os
from setuptools import setup, find_packages

MODULE = 'collecting_society_portal'
PREFIX = 'c3s'

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGELOG.rst')) as f:
    CHANGELOG = f.read()

install_requires = [
    'colander',
    'c3s_collecting_society',
    'cornice',
    'cryptacular',
    'deform==2.0a2',
    'pyramid',
    'pyramid_beaker',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'pyramid_mailer',
    'trytond<3.6',
    'waitress',
]

test_requires = [
    'coverage',
    'nose',
    'webtest',
]

setup(
    name='%s_%s' % (PREFIX, MODULE),
    version='0.1',
    description=(
        'Web portal including: Tryton wrapper, Web user management, ',
        'Web frontend, Plugin system.'
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
    url='https://github.com/C3S/collecting_society.portal',
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
