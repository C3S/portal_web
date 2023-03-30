# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

from contextlib import contextmanager

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


class BasePageElement(object):
    '''Base class for page elements'''

    def __init__(self, browser, locator):
        '''sets locator'''
        self.locator = locator
        self.browser = browser

    def __get__(self, obj, cls=None):
        '''returns self'''
        return self

    def __set__(self, obj, val):
        '''synonym to set() for convenience'''
        self.set(val)

    def __delete__(self, obj):
        '''deactivates delete'''
        pass

    def __call__(self):
        '''implement: return WebElement'''
        pass

    def get(self):
        '''implement: get content of WebElement (deform field)'''
        pass

    def getRo(self):
        '''implement: get content of WebElement (deform field readonly)'''
        pass

    def set(self, val):
        '''implement: set content of WebElement (deform field)'''
        pass

    @contextmanager
    def wait_for_page_load(self, timeout=30):
        old_page = self.browser.find_element(By.TAG_NAME, 'html')
        yield
        WebDriverWait(self.browser, timeout).until(
            expected_conditions.staleness_of(old_page)
        )
