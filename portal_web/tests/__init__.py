# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import os
import glob

from .config import testconfig


def delete_screenshots():
    """
    Deletes all screenshots of previous selenium tests.

    Deletes all `.png` files in the folder defined in `config.py`
    (client/screenshots/path).

    Deletion may be turned on/off in `config.py` (client/screenshots/reset).

    Returns:
        None.
    """
    if testconfig['client']['screenshots']['reset']:
        path = os.path.join(
            testconfig['client']['screenshots']['path'], '*.png'
        )
        for screenshot in glob.glob(path):
            os.unlink(screenshot)


# Delete screenshots on each run of nosetests before the tests.
delete_screenshots()
