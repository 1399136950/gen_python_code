import re
import json
import collections
import inspect
import functools


INNER_ARGV = {'id', 'def', 'class', 'dict', 'list', 'str'}   # python 内置关键字
API_LIB_PREF = 'platform_api'   # python接口地址，用于类代码生成
SPACE = '    '  # 生成的python代码空白格式符
CLASS_SPACE = SPACE * 2
api_func_names = set()
class_func_names = set()


def type_check(func):
    """
    参数类型检查
    @param func: 原函数
    @return:
    """
    sign = inspect.signature(func)
    
    @functools.wraps(func)
    def warp(*args, **kw):
        params = sign.parameters
        for param, val in zip(params, args):
            if params[param].annotation is params[param].empty:
                continue
            if not isinstance(val, params[param].annotation):
                raise TypeError(f'param <{param}> expect type {params[param].annotation} not {type(val)}')
        for k in kw:
            if params[k].annotation is params[k].empty:
                continue
            if not isinstance(kw[k], params[k].annotation):
                raise TypeError(f'param <{k}> expect type {params[k].annotation} not {type(kw[k])}')
        rtv = func(*args, **kw)
        return rtv

    return warp


def make_argv_standard(src):
    """
    参数名和函数名标准化
    """
    if src.isupper():
        return src.lower()
    n, ans = len(src), ''
    for i in range(n):
        if src[i].isupper():
            if i > 0 and ans[-1] != '_':
                ans += '_'
            ans += src[i].lower()
        else:
            ans += src[i]
    if ans in INNER_ARGV:
        ans = ans + '_'
    return ans


@type_check
def gen_python_class_code(api_desc: str, req_path: str, args_info: collections.deque, default_args: list = None, default_args_address: int = 0):
    """
    @param api_desc: 接口描述
    @param req_path: 请求地址
    @param args_info: 参数信息 [参数变量名, 参数描述, 参数类型(body/header/), 是否必传, 参数数据类型, 是否包含嵌套, 参数等级(标识嵌套层级嵌套)]
    @param default_args: 默认参数
    @param default_args_address: 默认参数的位置, 0放到args_info的左边, 1放到args_info的右边
    """
    if type(args_info) == list or type(args_info) == tuple or type(args_info) == set:
        args_info = collections.deque(args_info)
    have_token = False
    standard_argv_dict = {argv.name: make_argv_standard(argv.name) for argv in args_info}
    if default_args is not None:
        standard_argv_dict.update({argv.name: make_argv_standard(argv.name) for argv in default_args})
        if default_args_address == 0:
            while default_args:
                _argv = default_args.pop()
                args_info.appendleft(_argv)
        else:
            while default_args:
                _argv = default_args.pop(0)
                args_info.append(_argv)
    if args_info and args_info[0][0] == 'token':
        have_token = True
        args_info.popleft()
    func_nam = make_argv_standard(req_path.split('/')[-2] + '_' + req_path.split('/')[-1])
    index = -3
    while func_nam in class_func_names:
        func_nam = make_argv_standard(req_path.split('/')[index] + '_' + func_nam)
        index -= 1
    class_func_names.add(func_nam)
    argv_list = []
    for argv in args_info:
        if argv.schema_type == '':
            if argv.data_type in {'str', 'int', 'bool'}:
                argv_list.append(f'{standard_argv_dict[argv.name]}: {argv.data_type}')
            else:
                argv_list.append(f'{standard_argv_dict[argv.name]}')
    if len(argv_list) > 0:
        argv_list_str = 'self, ' + ', '.join(argv_list)
    else:
        argv_list_str = 'self'
    contents = list()
    contents.append(f'{SPACE}def {func_nam}({argv_list_str}):')
    contents.append(CLASS_SPACE + '"""')
    contents.append(CLASS_SPACE+api_desc)
    for argv in args_info:
        if argv.schema_type == '':
            contents.append(f"{CLASS_SPACE}@param {standard_argv_dict[argv.name]}: {argv.desc}; 是否必传-{argv.is_must}; 类型-{argv.data_type}")
    contents.append(CLASS_SPACE+'"""')
    argv_name = ', '.join([standard_argv_dict[argv.name] for argv in args_info if argv.schema_type == ''])
    if have_token:
        if len(argv_name) > 0:
            argv_name = 'self.token, ' + argv_name
        else:
            argv_name = 'self.token'
    contents.append(CLASS_SPACE+f'res = {API_LIB_PREF}.{func_nam}({argv_name})')
    contents.append(CLASS_SPACE+'return res')
    contents.append('\n')
    return '\n'.join(contents)


@type_check
def gen_python_api_code(api_desc: str, req_type: str, req_path: str, req_data_type: str, args_info: collections.deque, default_args: list = None, default_args_address: int = 0):
    """
    @param api_desc: 接口描述
    @param req_type: 接口请求类型: POST/GET/DELETE
    @param req_path: 请求地址
    @param req_data_type: 请求数据类型 application/json
    @param args_info: 参数信息 [参数变量名, 参数描述, 参数类型(body/header/), 是否必传, 参数数据类型, 是否包含嵌套, 参数等级(标识嵌套层级嵌套)]
    @param default_args: 默认参数
    @param default_args_address: 默认参数的位置, 0放到args_info的左边, 1放到args_info的右边
    """
    if type(args_info) == list or type(args_info) == tuple or type(args_info) == set:
        args_info = collections.deque(args_info)
    standard_argv_dict = {argv.name: make_argv_standard(argv.name) for argv in args_info}
    if default_args is not None:
        standard_argv_dict.update({argv.name: make_argv_standard(argv.name) for argv in default_args})
        if default_args_address == 0:
            while default_args:
                _argv = default_args.pop()
                args_info.appendleft(_argv)
        else:
            while default_args:
                _argv = default_args.pop(0)
                args_info.append(_argv)
    func_nam = make_argv_standard(req_path.split('/')[-2] + '_' + req_path.split('/')[-1])
    index = -3
    while func_nam in api_func_names:
        func_nam = make_argv_standard(req_path.split('/')[index] + '_' + func_nam)
        index -= 1
    api_func_names.add(func_nam)
    argv_list = []
    for argv in args_info:
        if argv.schema_type == '':
            if argv.data_type in {'str', 'int', 'bool'}:
                argv_list.append(f'{standard_argv_dict[argv.name]}: {argv.data_type}')
            else:
                argv_list.append(f'{standard_argv_dict[argv.name]}')
    argv_list_str = ', '.join(argv_list)
    contents = list()
    contents.append(f'def {func_nam}({argv_list_str}):')
    contents.append(SPACE + '"""')
    contents.append(SPACE+api_desc)
    for argv in args_info:
        if argv.schema_type == '':
            contents.append(f"{SPACE}@param {standard_argv_dict[argv.name]}: {argv.desc};是否必传-{argv.is_must};类型-{argv.data_type}")
    contents.append(SPACE+'"""')
    contents.append(f"{SPACE}url = HOST + '{req_path}'")
    data = {}
    headers = {}
    data_parent = data
    headers_parent = headers
    prev_data_req_type = None
    for argv in args_info:
        if argv.req_type != '':
            prev_data_req_type = argv.req_type
        if prev_data_req_type == 'body' or prev_data_req_type == '' or prev_data_req_type == 'query' or prev_data_req_type == 'formData':
            if argv.level == '0' and argv.schema_type != '':
                continue
            if argv.schema_type != '':
                data_parent[argv.name] = {}
                data_parent = data_parent[argv.name]
            else:
                data_parent[argv.name] = standard_argv_dict[argv.name]
        elif prev_data_req_type == 'header':
            headers_parent[argv.name] = standard_argv_dict[argv.name]
        else:
            raise ValueError(f'unknow prev_data_req_type {prev_data_req_type}')
    data_json = re.sub(': "(.*?)"', r": \1", json.dumps(data))
    headers_json = re.sub(': "(.*?)"', r": \1", json.dumps(headers))
    send_data_key = 'data'
    if req_data_type == 'application/json':
        send_data_key = 'json'
    elif req_type.lower() == 'get':
        send_data_key = 'params'
    if data:
        contents.append(f"{SPACE}data = {data_json}")
    if headers:
        contents.append(f"{SPACE}headers = {headers_json}")
    if data and headers:
        contents.append(f"{SPACE}r = requests.{req_type.lower()}(url, {send_data_key}=data, headers=headers)")
    elif data:
        contents.append(f"{SPACE}r = requests.{req_type.lower()}(url, {send_data_key}=data)")
    elif headers:
        contents.append(f"{SPACE}r = requests.{req_type.lower()}(url, headers=headers)")
    else:
        contents.append(f"{SPACE}r = requests.{req_type.lower()}(url)")
    contents.append(f"{SPACE}r.close()")
    contents.append(f"{SPACE}return r.json()")
    contents.append("\n\n")
    return '\n'.join(contents)
