### 关于gen_python_code
适用基于`Knife4j`生成的java api文档， 运行selenium爬虫爬取接口文档，自动生成python接口代码, 减少人工编写接口函数的时间
生成两个文件: `api.py`和`user.py`, `api.py`为python接口函数, `user.py`为封装成类的代码
### 使用
将`spider.py`中的url改成要爬取的api文档链接, 运行`python spider.py`即可  
`spider.py`中的`API_MODULE`和`CLASS_MODULE`为默认的填充模板，填充在`api.py`和`user.py`的开头,可自行修改  
