#!/usr/bin/env python
# coding:utf8
import pexpect
import sys
import os
import re
import configparser
from functools import reduce
import json
from collections import defaultdict
from OLTinME60 import OLT
import urllib.request


def GetRawInterfaceInfo(ipAddress, loginName, loginPassword, cmd_list):
    # print(ipAddress, loginName, loginPassword, cmd_list)
    # 提示符，可能是’ $ ’ , ‘ # ’或’ > ’
    loginprompt = '[$#>]'
    # 拼凑 ssh 命令
    cmd = 'ssh {}@{}'.format(loginName, ipAddress)
    # 为 ssh 生成 spawn 类子程序
    child = pexpect.spawn(cmd)

    # 期待'Password'字符串出现，从而接下来可以输入密码
    index = child.expect(
        ["[pP]assword", "yes/no", pexpect.EOF, pexpect.TIMEOUT])
    if(index == 0):
        # 匹配'Password'字符串成功，输入密码.
        child.sendline(loginPassword)
        # 期待 "设备提示符" 出现.
        index = child.expect([loginprompt, pexpect.EOF, pexpect.TIMEOUT])
        if(index == 0):
            # print('成功登陆设备')
            result = []
            for cmd in cmd_list[0:-1]:
                # 期待 "设备提示符" 出现.
                child.sendline(cmd)
                index = child.expect(
                    [loginprompt, pexpect.EOF, pexpect.TIMEOUT])
                if(index == 0):
                    # pass
                    result.append(child.before.decode('utf-8'))
                else:
                    # 匹配到了 pexpect.EOF 或 pexpect.TIMEOUT，表示超时或者 EOF，程序打印提示信息并退出.
                    print("ssh login failed, due to TIMEOUT or EOF")
                    child.close(force=True)
            child.sendline(cmd_list[-1])
            # print(child.before.decode('utf-8'))
            # result = result + child.before.decode('utf-8')
        else:
            # 匹配到了 pexpect.EOF 或 pexpect.TIMEOUT，表示超时或者 EOF，程序打印提示信息并退出.
            print("ssh login failed, due to TIMEOUT or EOF")
            child.close(force=True)
    elif (index == 1):
        # 匹配'yes/no'字符串成功，输入yes.
        child.sendline("yes")
        index = child.expect(
            ["[pP]assword", "yes/no", pexpect.EOF, pexpect.TIMEOUT])
        if (index == 0):
            # 匹配'Password'字符串成功，输入密码.
            child.sendline(loginPassword)
            # 期待 "设备提示符" 出现.
            index = child.expect([loginprompt, pexpect.EOF, pexpect.TIMEOUT])
            # 匹配 "设备提示符" 成功，输入操作的命令.
            if(index == 0):
                result = []
                for cmd in cmd_list[:-1]:
                    # 期待 "设备提示符" 出现.
                    child.sendline(cmd)
                    index = child.expect(
                        [loginprompt, pexpect.EOF, pexpect.TIMEOUT])
                    if(index == 0):
                        # pass
                        result.append(child.before.decode('utf-8'))
                    else:
                        # 匹配到了 pexpect.EOF 或 pexpect.TIMEOUT，表示超时或者 EOF，程序打印提示信息并退出.
                        print("111: ssh login failed, due to TIMEOUT or EOF")
                        child.close(force=True)
                child.sendline(cmd_list[-1])
                # result = child.before.decode('utf-8')
            else:
                # 匹配到了 pexpect.EOF 或 pexpect.TIMEOUT，表示超时或者 EOF，程序打印提示信息并退出.
                print(
                    "222: ssh login failed, due to TIMEOUT or EOF {0}".format(index))
                child.close(force=True)
        else:
            # 匹配到了 pexpect.EOF 或 pexpect.TIMEOUT，表示超时或者 EOF，程序打印提示信息并退出.
            print("333: ssh login failed, due to TIMEOUT or EOF")
            child.close(force=True)
    else:
        # 匹配到了 pexpect.EOF 或 pexpect.TIMEOUT，表示超时或者 EOF，程序打印提示信息并退出.
        print("Content-type: text/html\n")
        print("444: ssh login failed, due to TIMEOUT or EOF -9 index={}".format(index))
        child.close(force=True)

    # print(f'result的长度是{len(result)}')
    _result = []

    # print(result[2])

    for line in result:
        _temp = line.split('\r\n')
        # 因ME60的版本不同，在命令返回一行字符超过80时，有不同的结果，需要分别处理
        # 先处理超过80个字符不换行，补空格的情况
        for item in _temp:
            if len(item) > 80:
                # print(f'{len(item)}  {item[:80]}{item[80:].replace(" ", "")}')
                _result.append(f'{item[:80]}{item[80:].replace(" ", "")}')
            else:
                # print(f'{len(item)}  {item}')
                _result.append(f'{item}')
        # _result.extend(_temp)

    # print(''.join(_result))

    # _result = result[2].split('\r\n')
    # print(f'按换行符分隔后的行数：{len(_result)}')
    # for item in _result:
    #     if len(item) > 80:
    #         print(f'{len(item)}  {item[:80]}{item[80:].replace(" ", "")}')
    #     else:
    #         print(f'{len(item)}  {item}')

    # 这里开始处理超过80个字符 换行+补空格的情况
    _tempRawInterfaceInfo = []
    process_ing = ''
    # regexp = re.compile(r' +')
    # 包含10个以上的空格开始的行，很可能是上一行没有显示完的剩余部分
    regexp = re.compile(r' {10,}')

    for item in _result:
        hasspace = regexp.match(item)
        if hasspace:
            # print('空格开始的行', end='')
            # 把此行和上一行拼接成一个完整的行
            _tempRawInterfaceInfo.append(
                f'{process_ing}{item.strip()}')
            process_ing = ''
        else:
            # print('非空格开始的行', end='')
            _tempRawInterfaceInfo.append(process_ing)
            process_ing = item
    hasspace = regexp.match(process_ing)
    if hasspace:
        pass
    else:
        _tempRawInterfaceInfo.append(process_ing)

    result = list(filter(lambda item: item, _tempRawInterfaceInfo))
    # for item in result:
    #     print(item)

    return '\r\n'.join(result)


if __name__ == '__main__':
    # sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer)

    # #获取post过来的数据
    # form = cgi.FieldStorage()
    # brasid = form.getvalue('brasid')

    brasid = sys.argv[1]
    config = configparser.ConfigParser()
    config.read('/var/www/html/cgi-bin/nasportid/brasinfo.conf', encoding='utf-8')

    style = config.get(brasid, 'style')
    name = config.get(brasid, 'name')
    ip = config.get(brasid, 'ip')
    loginName = config.get(brasid, 'loginName')
    loginPassword = config.get(brasid, 'loginPassword')
    prefix = config.get(brasid, 'prefix')
    cmd_list = ['screen-length 0 temporary',
                'display interface brief', 'dis interface description', 'quit']

    # 获取设备上命令返回的原始结果
    RawInterfaceInfo = GetRawInterfaceInfo(
        ip, loginName, loginPassword, cmd_list)
    print(RawInterfaceInfo)

    # print('#' * 40)
    # 获取olt相关的信息
    regexp = re.compile(
        r'(\S+) +(\S+) +(\S+) +(\S+)[-_](\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    interfaceInfo = regexp.findall(RawInterfaceInfo)
    olts = []

    for item in interfaceInfo:
        # print(item[4], item[3], item[0])
        if 'up' == item[1]:
            olts.append(OLT(item[4], item[3], item[0]))

    # print(len(olts))
    # print('#'*40)
    # for olt in olts:
    #     print(olt.IP, olt.Name, olt.FullPortName, olt.Nasport)

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
            if '/' in portname:
                # 如果是独立端口
                regexp = re.compile(r'(\d{1})/(\d{1})/(\d{1})')
                slot = regexp.findall(portname)
                # print(slot[0][0])
                _nasport = f'{prefix}:{slot[0][0]}_{slot[0][1]}/{slot[0][2]}'
                _nasportidlist = []
                _nasportidlist.append(_nasport)
                dic_NasPort[portname] = _nasportidlist
                # print(portname, _nasport)
            else:
                # 这里是聚合端口
                regexp1 = re.compile(r'(.+)(\d+)')
                slot = regexp1.findall(portname)
                # print(slot[0][0], slot[0][1])
                subinterface = slot[0][1]
                regexp2 = re.compile(f'{portname}[\\s\\S]*?{slot[0][0]}')
                slot = regexp2.findall(RawInterfaceInfo)
                # Eth-Trunk的组成
                Eth_Trunk_str = slot[0]
                _slotlist = []
                # 提取组成Eth-Trunk的槽位
                regexp3 = re.compile(r'(\d{1})\/\d{1}\/\d{1}')
                slot = regexp3.findall(Eth_Trunk_str)
                # 将组成聚合口的槽位信息存入临时列表中
                for item in slot:
                    # print(type(item))
                    _slotlist.append(item)
                slotlist = list(set(_slotlist))
                slotlist.sort()
                _nasportidlist = []
                for slot in slotlist:
                    # print(f'{slot}_2/{subinterface}')
                    _nasportidlist.append(
                        f'{prefix}:{slot}_2/{subinterface}')

                # 将聚合口的组成信息填入字典中
                # dic_NasPort[portname] = ';'.join(_nasportidlist)
                dic_NasPort[portname] = _nasportidlist

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

    # 调整olt.Name为中文
    ip_key = dic_olts.keys()
    for key in ip_key:
        if key in oltswithall:
            dic_olts[key]['name'] = oltswithall[key]['name']
            dic_olts[key]['vlan'] = oltswithall[key]['vlan']
            dic_olts[key]['domain'] = oltswithall[key]['domain']
            dic_olts[key]['type'] = oltswithall[key]['type']
            dic_olts[key]['pppoebras'] = [ip]

    # # print(dic_olts)

    # 这里尝试把olt.Name为undefinded的数据，从olts列表中去除(这部分不是olt)
    _dic_olts = [{ip: dic_olts[ip]}
                 for ip in dic_olts if dic_olts[ip]['name'] != 'undefined']

    dic_olts = {}
    for item in _dic_olts:
        dic_olts.update(item)

    # 将信息写入文件中
    with open(f"/var/www/html/cgi-bin/nasportid/{brasid}.json", "w") as f:
        f.write(json.dumps(dic_olts))
