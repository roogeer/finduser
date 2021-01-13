#!/usr/bin/env python
# coding:utf-8
from collections import defaultdict
import re
import os
import json
import logging

def GetFiles(path):
    _filename = []
    for file in os.listdir(path):
        if os.path.splitext(file)[1] == '.json':
            file_path = os.path.join(path, file)
            _filename.append(file_path)
    return _filename


jsonfiles = GetFiles(r"/var/www/html/cgi-bin/nasportid")
# jsonfiles.remove(r'/var/www/html/oltnasportid.json')
jsonfiles.sort()

# 创建一个logging对象
logger = logging.getLogger()
# 创建一个文件对象  创建一个文件对象,以UTF-8 的形式写入 标配版.log 文件中
fh = logging.FileHandler('/var/www/html/error.log', encoding='utf-8')
# 配置显示格式  可以设置两个配置格式  分别绑定到文件和屏幕上
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
fh.setFormatter(formatter)  # 将格式绑定到两个对象上

logger.addHandler(fh)   # 将两个句柄绑定到logger

logger.setLevel(10)   # 总开关
fh.setLevel(10)  # 写入文件的从10开始

# logging.error('error message')

# 逐一加载json文件，根据ip，合并nasportid信息
dic_olts = {}
for jsonfile in jsonfiles:
    # print(jsonfile)
    with open(jsonfile, "r", encoding='utf-8') as f:
        _dic_olts = json.load(fp=f)
        for ip, value in _dic_olts.items():
            # print(ip, value)
            if ip in dic_olts:
                try:
                    # print(jsonfile, ip)
                    # 如果ip在结果字典中，合并nasportid字段，合并bras字段，合并interface字段
                    dic_olts[ip]['nasportid'].extend(value['nasportid'])
                    dic_olts[ip]['bras'].update(value['bras'])
                    dic_olts[ip]['pppoebras'].extend(value['pppoebras'])
                    # dic_olts[ip]['interface'].update(value['interface'])
                except KeyError as err:
                    print(f'{jsonfile}  {ip}-->{dic_olts[ip]["name"]}, KeyError {err}')
                    logging.error(f'{jsonfile}  {ip}-->{dic_olts[ip]["name"]}, KeyError {err}')
            else:
                # 如果ip不在结果字典中，添加进结果表
                dic_olts[ip] = value

# 对dic_olts按名称排序
_dic_olts = list(sorted(dic_olts.items(), key=lambda item: item[1]['name']))

# 将上述结果的list转为dict
dic_olts = {}
for item in _dic_olts:
    dic_olts[item[0]] = item[1]
    # print(type(item), item)

# 将信息写入文件中
with open(r"/var/www/html/oltnasportid.json", "w") as f:
    f.write(json.dumps(dic_olts))

# 在屏幕上打印，以方便核查
for key, value in dic_olts.items():
    try:
        print(key, value['name'], value['type'], ';'.join(value['nasportid']))
    except KeyError as err:
        print(f'{key}  {value["name"]}-->, KeyError {err}')
        logging.error(f'{key}  {value["name"]}-->, KeyError {err}')
