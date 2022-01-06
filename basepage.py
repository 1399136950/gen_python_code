from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
import os


CHROME_DRIVER_PATH = os.path.abspath('./chromedriver.exe')


class BasePage:

    def __init__(self, timeout=10, **kw):
        self.driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, **kw)
        self.timeout = timeout
        
    def __getattr__(self, name):
        return getattr(self.driver, name)

    def _find_element(self, mode, val):
        ele = WebDriverWait(self.driver, self.timeout).until(ec.presence_of_element_located((mode, val)))
        return ele
        
    def find_element(self, model, val):
        return self._find_element(model, val)
        
    def find_elements(self, model, val):
        return self._find_elements(model, val)
        
    def _find_elements(self, mode, val):
        ele_list = WebDriverWait(self.driver, self.timeout).until(ec.presence_of_all_elements_located((mode, val)))
        return ele_list
