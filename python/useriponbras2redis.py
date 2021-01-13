#!/usr/bin/env python
# coding:utf8
import pexpect
import configparser
import re
from useriponbrastools import *
from collections import defaultdict
import json
from IPy import IP, IPSet
import redis
import logging


def getUseripFromBras(brasName):
    dic_BRAS_COMMAND = {
        "7750": ['environment no more', 'show router dhcp local-dhcp-server "server1" summary', 'logout'],
        "me60": ['screen-length 0 temporary', 'display ip pool', 'quit'],
        "redback": ['terminal length 0', 'context pppoe', 'show ip interface brief', 'exit']
    }

    dic_REGEXP = {
        "7750": '(Pool name\W+(pppoe)-default-\S+[\s\S]*?Totals for pool)|(Pool name\W+(game)\d{1,}[\s\S]*?Totals for pool)|(Pool name\W+(business)[\s\S]*?Totals for pool|Pool name\W+(vip10)[\s\S]*?Totals for pool)|(Pool name\W+(vip3)[\s\S]*?Totals for pool)|(Pool name\W+(vip1)[\s\S]*?Totals for pool)|(Pool name\W+(iptv)[\s\S]*?Totals for pool)',
        "redback": '(pool)\S+\s+(\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\S+)|(Game)Vip1\s+(\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\S+)|SheQu(Vip1)\s+(\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\S+)|SheQu(Vip3)\s+(\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\S+)|(business)\s+(\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\S+)|(iptv)\S+\s+(\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\S+)|(vip10)\s+(\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\S+)',
        "me60": 'Pool-Name\s+: (business)\S+[\s\S]*?Gateway\s+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}).+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,})|Pool-Name\s+: (game)\S+[\s\S]*?Gateway\s+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}).+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,})|Pool-Name\s+: (iptv)[\s\S]*?Gateway\s+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}).+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,})|Pool-Name\s+: (vip1)\S+[\s\S]*?Gateway\s+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}).+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,})|Pool-Name\s+: (vip3)[\s\S]*?Gateway\s+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}).+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,})|Pool-Name\s+: pppoe-(vip10)[\s\S]*?Gateway\s+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}).+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,})|Pool-Name\s+: (pppoe)-user-pool\S+[\s\S]*?Gateway\s+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}).+: (\d{1,}\.\d{1,}\.\d{1,}\.\d{1,})'
    }

    brasid = brasName
    config = configparser.ConfigParser()
    config.read(r'/var/www/html/cgi-bin/brasinfo.conf', encoding='utf-8')

    style = config.get(brasid, 'style')
    # name = config.get(brasid, 'name')
    ip = config.get(brasid, 'ip')
    loginName = config.get(brasid, 'loginName')
    loginPassword = config.get(brasid, 'loginPassword')
    cmd_list = dic_BRAS_COMMAND[style]

    # LJS7750的命令需要调整，并确定需要使用的正则表达式
    if 'LJS-7750-1' == brasid:
        cmd_list[1] = 'show router dhcp local-dhcp-server "whgwbn" summary'

    regex = dic_REGEXP[style]

    # print(brasid, name, style, ip, loginName, loginPassword)
    # for item in cmd_list:
    #     print(item)

    rawinfo = GetRawInfo(ip, loginName, loginPassword, cmd_list)
    # print(rawinfo)

    pool_address = defaultdict(list)

    # 准备开始提取7750上的地址池
    # regex = r'(Pool name\W+(pppoe)-default-\S+[\s\S]*?Totals for pool)|(Pool name\W+(game)\d{1,}[\s\S]*?Totals for pool)|(Pool name\W+(business)[\s\S]*?Totals for pool|Pool name\W+(vip10)[\s\S]*?Totals for pool)|(Pool name\W+(vip3)[\s\S]*?Totals for pool)|(Pool name\W+(vip1)[\s\S]*?Totals for pool)|(Pool name\W+(iptv)[\s\S]*?Totals for pool)'
    result = re.findall(regex, rawinfo)
    if 'me60' == style:
        # ME60
        for pool_segment in result:
            # 清除正则表达式返回结果中的空元素
            pool_segment = [item for item in pool_segment if item]
            # 提取地址池名称，ip，掩码
            poolName, ip, mask = pool_segment
            # 地址池名称转为小写
            poolName = poolName.lower()
            # 将掩码形式转为后缀形式
            ipaddress = IP(ip).make_net(mask)
            # print(poolName, ipaddress.strNormal())
            pool_address[poolName].append(ipaddress.strNormal())
    elif '7750' == style:
        # 7750
        for pool in result:
            pool_segment = [item for item in pool if item]
            poolName = pool_segment[1].lower()
            poolStr = pool_segment[0]
            # 提取每个地址pool name下的具体地址段
            ipaddress = re.findall(
                r'\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\/\d{1,}', poolStr)
            # print(poolName, ipaddress)
            pool_address[poolName].extend(ipaddress)
    else:
        # redback
        for pool_segment in result:
            # 大写转小写
            pool_network = [item.lower() for item in pool_segment if item]
            # pool转pppoe
            pool_network = list(
                map(lambda x: 'pppoe' if x == 'pool' else x, pool_network))
            # 将ip地址-1形成合法的网络地址
            ip, mask = pool_network[1].split('/')
            ip_a, ip_b, ip_c, ip_d = ip.split('.')
            ipaddress = f'{ip_a}.{ip_b}.{ip_c}.{int(ip_d)-1}/{mask}'
            # print(temp_list[0], temp_list[1])
            pool_address[pool_network[0]].append(ipaddress)

    return pool_address


if __name__ == '__main__':
    BRASNAME = [
        'CQ-7750-1',
        'CQ-ME60-1',
        'CQ-ME60-2',
        'CQ-ME60-3',
        'CQ-ME60-4',
        'CQ-ME60-5',
        'CQ-ME60-6',
        'CQ-ME60-7',
        'CQ-ME60-9',
        'CQ-ME60-10',
        'LJS-7750-1',
        'LJS-ME60-1',
        'LJS-ME60-2',
        'LJS-ME60-3',
        'LJS-ME60-4',
        'LJS-ME60-5',
        'XD-ME60-1',
        'XD-ME60-2',
        '116-ME60-1',
        '116-ME60-2',
        'HY-ME60-1',
        'HY-ME60-2',
        'JZ-7750-1',
        'JZ-Redback',
        'HS-ME60-1',
        'HS-ME60-2',
        'EZ-Redback',
        'XG-7750-1'
    ]

    useriponbras = defaultdict(list)
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    for bras in BRASNAME:
        # 获取指定bras上的用户ip
        userip = getUseripFromBras(bras)
        # 将同类型的地址池归类{pppoe, vip1, vip3, vip10, game, iptv, business}
        useriponbras['pppoe'].extend(userip['pppoe'])
        useriponbras['vip1'].extend(userip['vip1'])
        useriponbras['vip3'].extend(userip['vip3'])
        useriponbras['vip10'].extend(userip['vip10'])
        useriponbras['game'].extend(userip['game'])
        useriponbras['iptv'].extend(userip['iptv'])
        useriponbras['business'].extend(userip['business'])

        # 打开文件准备写入
        filename = f'/var/www/html/userip_{bras}.json'
        with open(filename, "w") as f:
            f.write(json.dumps(userip, indent=2))

        # 写入redis
        r.set(f'userip_{bras}', json.dumps(userip))

    # 对所有网段进行扫描，不应该出现重复的网段
    all_ipaddress = []
    for pool, ips in useriponbras.items():
        for ip in ips:
            all_ipaddress.append(ip)

    # 创建一个logging对象
    logger = logging.getLogger()
    # 创建一个文件对象  创建一个文件对象,以UTF-8 的形式写入 标配版.log 文件中
    fh = logging.FileHandler(
        '/var/www/html/useriponbras.log', encoding='utf-8')
    # 配置显示格式  可以设置两个配置格式  分别绑定到文件和屏幕上
    formatter = logging.Formatter(
        '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    fh.setFormatter(formatter)  # 将格式绑定到两个对象上

    logger.addHandler(fh)   # 将两个句柄绑定到logger

    logger.setLevel(10)   # 总开关
    fh.setLevel(10)  # 写入文件的从10开始

    ips_len = len(all_ipaddress)
    for i in range(ips_len):
        for j in range(i+1, ips_len):
            if IP(all_ipaddress[i]).overlaps(all_ipaddress[j]) != 0:
                # print(a[i],a[j])
                logging.error(
                    f'{all_ipaddress[i]}与{all_ipaddress[j]}重复或是互相包含，需要检查配置')

    # 对ip地址进行聚合
    useriponbras_aggregation = defaultdict(list)
    for pool, ips in useriponbras.items():
        # print(pool, ips)
        # 分别对不同类型的地址池进行聚合
        result = IPSet()
        for ip in ips:
            result.add(IP(ip))
        # 将聚合后的结果存入useriponbras_aggregation
        for item in result:
            useriponbras_aggregation[pool].append(item.strNormal(
                1) + '/32' if('/' not in item.strNormal(1)) else item.strNormal(1))

    # print(json.dumps(useriponbras_aggregation, indent=2))
    filename = f'/var/www/html/useriponbras.json'
    with open(filename, "w") as f:
        f.write(json.dumps(useriponbras_aggregation, indent=2))

    # 写入redies
    r.set(f'useriponbras_aggregation', json.dumps(useriponbras_aggregation))
