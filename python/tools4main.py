#!/usr/bin/env python
# coding:utf8
import pexpect
import configparser
import re
import redis
from IPy import IP
import json
from ipcrossnat import *


def getUsername(userip):
    # 根据用户ip，查询到ip所在的bras
    brasname = getBrasNameFromIP(userip)
    if not brasname:
        # 非有效的用户ip，返的对象中，username为空值
        # return ''
        return {
            'success': False,
            'info': {
                'brasip': '-',
                'brasname': '-',
                'cevlan': '-',
                'detail': '非用户ip',
                'hillstone': '-',
                'interface': '-',
                'nasportid': '-',
                'oltip': '-',
                'oltname': '-',
                'onu': '-',
                'panabit': '-',
                'pevlan': '-',
                'pon': '-',
                'pool': '-',
                'qos': '-',
                'userip': userip,
                'username': '-'
            }
        }

    # 登录指定的bras, 根据ip查找用户帐号
    # bras上用到的相关命令
    dic_BRAS_COMMAND = {
        "7750": ['environment no more', 'show service id 100 ppp session ip-address userip | match userip pre-lines 2', 'logout'],
        "me60": ['screen-length 0 temporary', 'display access-user ip-address userip | include User name', 'quit'],
        "redback": ['terminal length 0', 'context pppoe', 'show subscribers active | grep options -B11 "userip "', 'exit']
    }

    # 对命令结果使用的正则表达式，提取用户帐号
    dic_BRAS_STYLE2REG = {
        "7750": r'pre-lines 2 *(?P<username>\S+) *svc',
        "me60": r'User name *: *(?P<username>\S+)',
        "redback": r'" {1,}(?P<username>\S+) *Session'
    }

    brasid = brasname
    config = configparser.ConfigParser()
    config.read(r'/var/www/html/cgi-bin/brasinfo.conf', encoding='utf-8')

    style = config.get(brasid, 'style')
    name = config.get(brasid, 'name')
    ip = config.get(brasid, 'ip')
    loginName = config.get(brasid, 'loginName')
    loginPassword = config.get(brasid, 'loginPassword')
    # cmd_list = (config.get(brasid, 'cmd_list')[1:-1]).replace("'", "").split(',')
    cmd_list = dic_BRAS_COMMAND[style]
    # regexp = config.get(brasid, 'regexp')
    regexp = dic_BRAS_STYLE2REG[style]

    # 调整cmd_list
    if 'redback' == style:
        cmd_list[2] = cmd_list[2].replace('userip', userip)
    else:
        cmd_list[1] = cmd_list[1].replace('userip', userip)

    # print(style, name, ip, loginName, loginPassword, cmd_list, regexp)

    RawInfo = GetRawInfo(ip, loginName, loginPassword, cmd_list)
    # print(RawInfo)
    # 将命令中的换行回车符，替换为空格，以方便使用正则表达式
    RawInfo = RawInfo.replace(chr(13), chr(32))
    RawInfo = RawInfo.replace(chr(10), chr(32))
    # print(RawInfo)
    # for ch in RawInfo:
    #     print(f'{ch}:{ord(ch)} ', end='')
    # print(regexp)
    result = re.search(regexp, RawInfo)
    try:
        dic_result = result.groupdict()
    except AttributeError:
        # 到这里用户不在线，但ip有效，可根据ip，brasid，查询该ip所穿越的nat设备信息
        hillstone, panabit = getUseripCrossHillstonePa(
            userip, brasid).split('_')
        # 判断ip所属的地址池
        # poolName = getUseripPoolNameFromAggregation(userip)
        poolName = getUseripPoolName(userip, brasid)
        # return ''
        return {
            'success': False,
            'info': {
                'brasip': ip,
                'brasname': name,
                'cevlan': '-',
                'detail': '未分配给用户',
                'hillstone': hillstone,
                'interface': '-',
                'nasportid': '-',
                'oltip': '-',
                'oltname': '-',
                'onu': '-',
                'panabit': panabit,
                'pevlan': '-',
                'pon': '-',
                'pool': poolName,
                'qos': '-',
                'userip': userip,
                'username': '-'
            }
        }
    # 到这里，查询到了在线用户的帐号
    # return dic_result['username']
    return {
        'success': True,
        'info': {
            'brasip': '',
            'brasname': '',
            'cevlan': '',
            'detail': '',
            'hillstone': '',
            'interface': '',
            'nasportid': '',
            'oltip': '',
            'oltname': '',
            'onu': '',
            'panabit': '',
            'pevlan': '',
            'pon': '',
            'pool': '',
            'qos': '',
            'userip': '',
            'username': dic_result['username']
        }
    }


def getBrasNameFromIP(userip):
    # 从redis中加载所有bras的地址信息，判断ip是否包含在某段地址中
    keys = [
        "userip_CQ-7750-1",
        "userip_CQ-ME60-1",
        "userip_CQ-ME60-2",
        "userip_CQ-ME60-3",
        "userip_CQ-ME60-4",
        "userip_CQ-ME60-5",
        "userip_CQ-ME60-6",
        "userip_CQ-ME60-7",
        "userip_CQ-ME60-9",
        "userip_CQ-ME60-10",
        "userip_LJS-7750-1",
        "userip_LJS-ME60-1",
        "userip_LJS-ME60-2",
        "userip_LJS-ME60-3",
        "userip_LJS-ME60-4",
        "userip_LJS-ME60-5",
        "userip_XD-ME60-1",
        "userip_XD-ME60-2",
        "userip_116-ME60-1",
        "userip_116-ME60-2",
        "userip_HY-ME60-1",
        "userip_HY-ME60-2",
        "userip_HS-ME60-1",
        "userip_HS-ME60-2",
        "userip_JZ-7750-1",
        "userip_JZ-Redback",
        "userip_XG-7750-1",
        "userip_EZ-Redback"
    ]
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    for key in keys:
        # print(key)
        dic_ip_pool = json.loads(r.get(key).decode('utf-8'))
        for poolName, ips in dic_ip_pool.items():
            for ip in ips:
                if IP(userip).overlaps(ip):
                    return (key.split('_')[1])


def getUseripCrossHillstonePa(Userip, Brasid):
    return getHS_PA(Userip, Brasid)


def GetRawInfo(ipAddress, loginName, loginPassword, cmd_list):
    #print(ipAddress, loginName, loginPassword, cmd_list)
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
            #result = result + child.before.decode('utf-8')
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
                #result = child.before.decode('utf-8')
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

    return ''.join(result)


def getUseripPoolName(Userip, Brasid):
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    useriponbras = json.loads(r.get(f'userip_{Brasid}').decode('utf-8'))
    # print(useriponbras)
    for pool, ips in useriponbras.items():
        for ip in ips:
            if IP(Userip) in IP(ip):
                return pool
    return '-'


# def getUseripPoolNameFromAggregation(Userip):
#     r = redis.Redis(host='127.0.0.1', port=6379, db=0)
#     useriponbras = json.loads(
#         r.get(f'useriponbras_aggregation').decode('utf-8'))
#     # print(useriponbras)
#     for pool, ips in useriponbras.items():
#         for ip in ips:
#             if IP(Userip) in IP(ip):
#                 return pool
#     return '-'


def GetIpInfo(RawInfo, RegExp4IpQos, BrasName, BrasIp, Brasid):
    # 从RawInfo字符串中，提取用户ip和产品属性
    # BrasName  bras的中文名称
    # BrasIp    bras的登录ip
    # Braid     bras的配置文件关键字
    regexp = re.compile(RegExp4IpQos)
    result = re.search(regexp, RawInfo)
    try:
        dic_result = result.groupdict()
        dic_result['brasname'] = BrasName
        dic_result['brasip'] = BrasIp

        # 用户在线，还需要进一步判断ip所属的地址池
        # print(getUseripPoolName(dic_result['userip'], Brasid))
        dic_result['pool'] = getUseripPoolName(dic_result['userip'], Brasid)
        # 用户在线，还需要进一步判断ip所走的Hillstone和Panabit
        hillstone, panabit = getUseripCrossHillstonePa(
            dic_result['userip'], Brasid).split('_')
        # print(hillstone, panabit)
        dic_result['hillstone'] = hillstone
        dic_result['panabit'] = panabit
    except AttributeError:
        dic_result = {
            'interface': '-',
            'userip': '-',
            'qos': '-',
            'brasname': '-',
            'brasip': '-',
            'pool': '-',
            'hillstone': '-',
            'panabit': '-'
        }
    finally:
        return dic_result


def getUserIpInfo(username, nasportid):
    # 在指定的bras上，查询username是否在线，
    # 如果用户在线，返回用户ip、产品属性、穿越的hillstone和pababit
    dic_NASPORTID = {
        "WH-CQ-BR7750-1": "CQ-7750-1",
        "WH-CQ-ME60-1": "CQ-ME60-1",
        "WH-CQ-ME60-10": "CQ-ME60-10",
        "WH-CQ-ME60-2": "CQ-ME60-2",
        "WH-CQ-ME60-3": "CQ-ME60-3",
        "WH-CQ-ME60-4": "CQ-ME60-4",
        "WH-CQ-ME60-5": "CQ-ME60-5",
        "WH-CQ-ME60-6": "CQ-ME60-6",
        "WH-CQ-ME60-7": "CQ-ME60-7",
        "WH-CQ-ME60-9": "CQ-ME60-9",
        "WH-HS-ME60-1": "HS-ME60-1",
        "WH-HS-ME60-2": "HS-ME60-2",
        "WH-HY-ME60-1": "HY-ME60-1",
        "WH-HY-ME60-2": "HY-ME60-2",
        "WH-JZ-BR7750-1": "JZ-7750-1",
        "WH-LJS-BR7750-1": "LJS-7750-1",
        "WH-LJS-ME60-1": "LJS-ME60-1",
        "WH-LJS-ME60-2": "LJS-ME60-2",
        "WH-LJS-ME60-3": "LJS-ME60-3",
        "WH-LJS-ME60-4": "LJS-ME60-4",
        "WH-LJS-ME60-5": "LJS-ME60-5",
        "WH-QS116-ME60-1": "116-ME60-1",
        "WH-QS116-ME60-2": "116-ME60-2",
        "WH-Red-EZ-A": "EZ-Redback",
        "WH-Red-JZ-A": "JZ-Redback",
        "WH-XD-ME60": "XD-ME60-1",
        "WH-XD-ME60-2": "XD-ME60-2",
        "WH-XG-BR7750-1": "XG-7750-1"
    }

    # 7750: 直接使用正则, {qos, ip}
    # me60: 需要在正则前面加上用户帐号, {qos, ip}
    # redback: 直接使用正则,{ip, qos}
    dic_BRAS_STYLE2REG = {
        "7750": 'Description.+sap:\[(?P<interface>\S+):[\s\S]*?SLA-Profile-String\W+"(?P<qos>.+)"[\s\S]*IP Address\W+(?P<userip>\d{1,}\.\d{1,}\.\d{1,}\.\d{1,})',
        "me60": ' +(?P<interface>\S+) +(?P<userip>\S+)[\s\S].+[\s\S]*?\W+(?P<qos>\S+)',
        "redback": 'Circuit +(?P<interface>\S+) vlan-id[\s\S]*?ip address (?P<userip>\S+)[\s\S]*?qos-metering-policy (?P<qos>\S+)'
    }

    dic_BRAS_COMMAND = {
        "7750": ['environment no more', 'show service id 100 ppp session user-name userid detail | match "IP Address" pre-lines 33', 'logout'],
        "me60": ['screen-length 0 temporary', 'dis access-user username userid item qos-profile', 'quit'],
        "redback": ['terminal length 0', 'context pppoe', 'show subscribers active username userid', 'exit']
    }

    try:
        brasid = dic_NASPORTID[nasportid]
        config = configparser.ConfigParser()
        config.read(r'/var/www/html/cgi-bin/brasinfo.conf', encoding='utf-8')

        style = config.get(brasid, 'style')
        name = config.get(brasid, 'name')
        ip = config.get(brasid, 'ip')
        loginName = config.get(brasid, 'loginName')
        loginPassword = config.get(brasid, 'loginPassword')
        # cmd_list = (config.get(brasid, 'cmd_list')[1:-1]).replace("'", "").split(',')
        cmd_list = dic_BRAS_COMMAND[style]
        # regexp = config.get(brasid, 'regexp')
        regexp = dic_BRAS_STYLE2REG[style]
        if 'me60' == style:
            regexp = f'\\d{{1,}} +{username}{regexp}'

        # 调整cmd_list
        if 'redback' == style:
            cmd_list[2] = cmd_list[2].replace('userid', username)
        else:
            cmd_list[1] = cmd_list[1].replace('userid', username)

        # print(style, name, ip, loginName, loginPassword, cmd_list, regexp)

        # return GetRawInfo(ip, loginName, loginPassword, cmd_list)
        RawInfo = GetRawInfo(ip, loginName, loginPassword, cmd_list)
        return GetIpInfo(RawInfo, regexp, name, ip, brasid)
    except KeyError:
        return {
            'interface': '-',
            'userip': '-',
            'qos': '-',
            'brasname': '-',
            'brasip': '-',
            'pool': '-',
            'hillstone': '-',
            'panabit': '-'
        }


if __name__ == '__main__':
    # userip = '118.145.128.9'
    # brasname = getBrasNameFromIP(userip)
    # print(brasname)

    # userip = '10.203.1.234'
    # brasname = 'JZ-7750-1'
    # userip = '10.203.1.234'
    # brasname = '116-ME60-1'
    # userip = '211.161.164.205'
    # brasname = 'JZ-Redback'
    # username = getUsername(userip)
    # print(username)

    # username = '24027000374302'
    # nasportid = 'WH-LJS-ME60-2'
    # rawinfo = getUserIpInfo(username, nasportid)
    # print(rawinfo)

    # username = '140270019328'
    # nasportid = 'WH-CQ-BR7750-1'
    # rawinfo = getUserIpQos(username, nasportid)
    # print(rawinfo)

    username = '140270001644'
    nasportid = 'WH-LJS-BR7750-1'
    rawinfo = getUserIpInfo(username, nasportid)
    print(rawinfo)
