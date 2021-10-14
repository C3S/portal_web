# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web


class BasePageElement(object):
    '''Base class for page elements'''

    def __init__(self, test, locator):
        '''sets locator'''
        self.locator = locator
        self.test = test
        self.cli = test.cli

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
