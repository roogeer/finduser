#!/usr/bin/env python
# coding:utf8
import sys
import os
import re
import configparser
from functools import reduce
import json
from collections import defaultdict
from OLTinRB import OLT
import urllib.request

if __name__ == '__main__':
    brasid = sys.argv[1]
    config = configparser.ConfigParser()
    config.read('/var/www/html/cgi-bin/nasportid/brasinfo.conf', encoding='utf-8')

    style = config.get(brasid, 'style')
    name = config.get(brasid, 'name')
    ip = config.get(brasid, 'ip')
    loginName = config.get(brasid, 'loginName')
    loginPassword = config.get(brasid, 'loginPassword')
    prefix = config.get(brasid, 'prefix')

    olts = []
    # 处理配置文件中预定义的olt
    predefined_olt = (config.get(
        brasid, 'predefined')[1:-1]).replace("'", "").split(',')

    # 如果配置文件中的predefined为空，需要进行以下处理
    predefined_olt = list(filter(lambda item: item, predefined_olt))
    # print(predefined_olt, type(predefined_olt), len(predefined_olt))
    for item in predefined_olt:
        regexp = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) +(\S+)')
        oltinfo = regexp.findall(item)
        # print(item, oltinfo[0][0], oltinfo[0][1])
        olts.append(OLT(oltinfo[0][0], 'undefined', oltinfo[0][1]))

    # print(len(olts))
    # print('#'*40)
    # for olt in olts:
    #     print(olt.IP, olt.Name, olt.FullPortName, olt.Nasport)

    # for olt in olts:
    #     print(olt.ip, olt.Nasport)

    # 根据olt的NasPort信息，生成与bras相关的NasPortID
    # 准备字典
    dic_NasPort = defaultdict(lambda: '')
    for olt in olts:
        portname = olt.Nasport
        # 如果olt的端口已经在字典中
        if portname in dic_NasPort:
            # olt.NasportID.append(dic_NasPort[portname])
            olt.NasportID.extend(dic_NasPort[portname])
        else:
            # 如果portname不在字典中，表示是第一次遇到该端口，需要生成NasportID到字典中
            _nasport = f'{prefix}:{olt.Nasport}'
            _nasportidlist = []
            _nasportidlist.append(_nasport)
            dic_NasPort[portname] = _nasportidlist
            # if '/' in portname:
            #     # 如果是独立端口
            #     regexp = re.compile(r'(\d{1,})/(\d{1,})')
            #     slot = regexp.findall(portname)
            #     # print(slot[0][0])
            #     _nasport = f'{prefix}:{slot[0][0]}_{slot[0][1]}/{slot[0][2]}'
            #     _nasportidlist = []
            #     _nasportidlist.append(_nasport)
            #     dic_NasPort[portname] = _nasportidlist
            #     # print(portname, _nasport)
            # else:
            #     # 这里是聚合端口，但是RedBack没有聚合端口，直接pass
            #     pass

            # 更新olt的nasportid信息
            olt.NasportID.extend(dic_NasPort[portname])

    # print(dic_NasPort)

    # 这里从192.168.108.79上提取raisecom的rcoltip2name信息，根据ip修改olt名称为中文
    url = "http://192.168.108.79:8983/rcoltip2name.json"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    data = resp.read().decode('utf-8')
    rcolts = json.loads(data)
    # print(olts)

    # 这里从192.168.108.81上提取greenway的gwoltip2name信息，根据ip修改olt名称为中文
    url = "http://192.168.108.81/gwoltip2name.json"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    data = resp.read().decode('utf-8')
    gwolts = json.loads(data)

    oltswithall = {}
    oltswithall.update(rcolts)
    oltswithall.update(gwolts)

    dic_olts = defaultdict(lambda: {})
    for olt in olts:
        # print(olt.ip, olt.Name, ';'.join(olt.NasportID), olt.FullPortName)
        if olt.ip in oltswithall:
            print(
                f'{olt.ip:18s} {oltswithall[olt.ip]["name"]:20s} {olt.Name} {olt.FullPortName}')
        else:
            print(f'{olt.ip:18s} 不是某台olt的ip')
        # print(olt.ip, olt.Name, olt.NasportID)
        # _nasportid = defaultdict(lambda: [])
        # _nasportid['nasportid'] = olt.NasportID

        # 如果olt是第一次出现
        if olt.ip not in dic_olts:
            dic_olts[olt.ip]['name'] = olt.Name
            dic_olts[olt.ip]['nasportid'] = olt.NasportID
            _dic_interface = defaultdict(lambda: {})
            _dic_interface[ip]['name'] = brasid
            _dic_interface[ip]['interface'] = [olt.FullPortName]
            dic_olts[olt.ip]['bras'] = _dic_interface
        else:
            dic_olts[olt.ip]['nasportid'].extend(olt.NasportID)
            dic_olts[olt.ip]['bras'][ip]['interface'].append(olt.FullPortName)

    # # 这里从192.168.108.79上提取raisecom的rcoltip2name信息，根据ip修改olt名称为中文
    # url = "http://192.168.108.79:8983/rcoltip2name.json"
    # req = urllib.request.Request(url)
    # resp = urllib.request.urlopen(req)
    # data = resp.read().decode('utf-8')
    # rcolts = json.loads(data)
    # # print(olts)

    # # 这里从192.168.108.81上提取greenway的gwoltip2name信息，根据ip修改olt名称为中文
    # url = "http://192.168.108.81/gwoltip2name.json"
    # req = urllib.request.Request(url)
    # resp = urllib.request.urlopen(req)
    # data = resp.read().decode('utf-8')
    # gwolts = json.loads(data)

    # olts = {}
    # olts.update(rcolts)
    # olts.update(gwolts)

    # 调整olt.Name为中文
    ip_key = dic_olts.keys()
    for key in ip_key:
        if key in oltswithall:
            dic_olts[key]['name'] = oltswithall[key]['name']
            dic_olts[key]['vlan'] = oltswithall[key]['vlan']
            dic_olts[key]['domain'] = oltswithall[key]['domain']
            dic_olts[key]['type'] = oltswithall[key]['type']
            if '10.207.7.111' == ip:
                # 荆州redback的pppoe ip地址
                dic_olts[key]['pppoebras'] = ['10.207.7.238']
            elif '10.207.7.112' == ip:
                # 鄂州redback的pppoe ip地址
                dic_olts[key]['pppoebras'] = ['10.207.7.237']
            else:
                pass

    # 这里尝试把olt.Name为undefinded的数据，从olts列表中去除(这部分不是olt)
    _dic_olts = [{ip: dic_olts[ip]}
                 for ip in dic_olts if dic_olts[ip]['name'] != 'undefined']

    dic_olts = {}
    for item in _dic_olts:
        dic_olts.update(item)

    # 将信息写入文件中
    with open(f"/var/www/html/cgi-bin/nasportid/{brasid}.json", "w") as f:
        f.write(json.dumps(dic_olts))
