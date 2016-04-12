# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import os
import glob

from .config import testconfig


def delete_screenshots():
    '''delete all screenshots of previous selenium tests'''
    if testconfig['client']['screenshots']['reset']:
        path = os.path.join(
            testconfig['client']['screenshots']['path'], '*.png'
        )
        for screenshot in glob.glob(path):
            os.unlink(screenshot)

delete_screenshots()
