import re
import logging
from time import sleep
import collections

from selenium.webdriver.common.action_chains import ActionChains

from basepage import BasePage
from make_python_code import gen_python_api_code, gen_python_class_code


Argv = collections.namedtuple('Argv', ['name', 'desc', 'req_type', 'is_must', 'data_type', 'schema_type', 'level'])
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s')
formatter.datefmt = '%Y-%m-%d %H:%M:%S'
sh.setFormatter(formatter)
logger.addHandler(sh)


def match_data_type(src):
    if src.find('string') > -1:
        return 'str'
    elif src.find('integer') > -1:
        return 'int'
    elif src.find('boolean') > -1:
        return 'bool'
    elif src.find('number') > -1:
        return 'int'
    return "'" + src + "'"


def match_req_data_type(src):
    return re.findall('((?:application|multipart)/.*?)$', src, re.DOTALL | re.IGNORECASE)[0]


API_MODULE = """import requests

from config.conf import PLATFORM_HOST as HOST


"""

CLASS_MODULE = """import api.platform.api as platform_api


class PlatFormUser:
    def __init__(self, phone, pwd):
        self.phone = phone
        self.pwd = pwd
        login_res = platform_api.home_login(phone, pwd)
        self.token = login_res['data']['token']

"""


if __name__ == '__main__':
    # url = 'http://192.168.1.87:8080/api/doc.html#/home'
    url = 'http://192.168.1.87:8008/admin/doc.html#/home'
    driver = BasePage()
    driver.driver.implicitly_wait(3)
    driver.get(url)
    driver.maximize_window()
    all_titles = driver.find_elements('css selector', 'li.ant-menu-submenu.ant-menu-submenu-inline')
    all_titles = all_titles[1:]
    api_fd = open('api.py', 'w', encoding='utf-8')
    user_fd = open('user.py', 'w', encoding='utf-8')
    api_fd.write(API_MODULE)
    user_fd.write(CLASS_MODULE)
    for title in all_titles:
        prev_class_len = 0
        prev_tab_len = 0
        logger.debug(f'-----{title.text}-----')
        title.click()
        ul = title.find_element('css selector', 'ul.ant-menu.ant-menu-inline.ant-menu-sub')
        li_list = ul.find_elements('tag name', 'li')
        sleep(1)
        for li in li_list:
            li.click()
            divs = driver.find_elements('css selector', 'div.knife4j-api-summary')
            while len(divs) == prev_class_len:
                sleep(0.2)
                divs = driver.find_elements('css selector', 'div.knife4j-api-summary')
            prev_class_len = len(divs)
            div = divs[-1]
            api_desc = li.text
            req_type = div.find_element('css selector', 'span.knife4j-api-summary-method').text  # post/get/delete
            req_path = div.find_element('css selector', 'span.knife4j-api-summary-path').text   # url
            req_data_type = match_req_data_type(driver.find_elements('css selector', 'div.ant-col.ant-col-12')[-2].text).lower()    # application/json/...
            logger.debug('%s %s %s %s', li.text, req_type, req_path, req_data_type)
            tables = driver.find_elements('css selector', 'tbody.ant-table-tbody')
            curr_tab_len = len(tables)
            table = tables[prev_tab_len - curr_tab_len]
            trs = table.find_elements('tag name', 'tr')
            args_info = collections.deque()
            token_index = None
            for tr in trs:
                level = tr.get_attribute('class')[-1]   # 参数级别
                tds = tr.find_elements('tag name', 'td')
                argv = tds[0].text   # 参数名
                desc = tds[1].text   # 参数描述
                argv_req_type = tds[2].text   # 参数请求类型，query/body/header
                is_must = tds[3].text    # 是否必须
                argv_data_type = match_data_type(tds[4].text)    # 参数数据类型 int, str, bool
                argv_schema_type = tds[5].text   # 参数的schema类型
                if argv == 'token':
                    args_info.appendleft(Argv(argv, desc, argv_req_type, is_must, argv_data_type, argv_schema_type, level))
                else:
                    args_info.append(Argv(argv, desc, argv_req_type, is_must, argv_data_type, argv_schema_type, level))
            api_content = gen_python_api_code(api_desc, req_type, req_path, req_data_type, args_info)
            class_content = gen_python_class_code(api_desc, req_path, args_info)
            api_fd.write(api_content)
            user_fd.write(class_content)
            api_fd.flush()
            user_fd.flush()
            prev_tab_len = curr_tab_len
        main_page = driver.find_element('css selector', 'span[pagekey="kmain"]')
        ActionChains(driver).context_click(main_page).perform()
        driver.find_elements('css selector', 'ul.contextmenu.ant-menu.ant-menu-vertical.ant-menu-root.ant-menu-light li')[2].click()
    api_fd.close()
    user_fd.close()
    driver.close()
    driver.quit()
