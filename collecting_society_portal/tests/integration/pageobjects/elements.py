# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

from selenium.common.exceptions import NoSuchElementException
import re

from .base import BasePageElement


class TextInputWidgetElement(BasePageElement):
    '''Deform TextInputWidget'''

    def __call__(self):
        return self.cli.find_element_by_id(self.locator)

    def get(self):
        return self().get_attribute("value")

    def getRo(self):
        return self().text

    def set(self, val):
        tf = self()
        tf.clear()
        tf.send_keys(val)


class TextAreaWidgetElement(TextInputWidgetElement):
    '''Deform TextAreaWidget'''
    pass


class HiddenWidgetElement(TextInputWidgetElement):
    '''Deform HiddenWidget'''

    def getRo(self):
        return self.get()


class PasswordWidgetElement(TextInputWidgetElement):
    '''Deform TextAreaWidget'''
    pass


class RadioChoiceWidgetElement(BasePageElement):
    '''Deform RadioChoiceWidget'''

    def __call__(self):
        '''returns radiobuttons'''
        rb = self.cli.find_elements_by_name(self.locator)
        if not rb:
            raise NoSuchElementException()
        return rb

    def get(self):
        for rb in self():
            if rb.is_selected():
                return rb.get_attribute("value")

    def getRo(self):
        '''returns iterator of option'''
        option = self.cli.find_elements_by_xpath(
            "//div[@id='item-"+self.locator+"']/div/p"
        )
        if len(option) == 1:
            return re.sub(
                self.locator+'-', '', option[0].get_attribute("id")
            )
        return False

    def set(self, val):
        '''val: iterator of option'''
        for rb in self():
            if rb.get_attribute("value") == val:
                rb.click()


class CheckboxChoiceWidgetElement(BasePageElement):
    '''Deform CheckboxChoiceWidget'''

    def __call__(self):
        return self.cli.find_element_by_id(self.locator)

    def get(self):
        return self().is_selected()

    def getRo(self):
        try:
            self()
            return True
        except:
            return False

    def set(self, val):
        if val is not self.get():
            self().click()


class ButtonElement(BasePageElement):
    '''Deform Button'''

    def __call__(self):
        self.cli.find_element_by_id(self.locator).click()
