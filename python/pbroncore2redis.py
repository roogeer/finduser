#!/usr/bin/env python
# coding:utf8
from pbroncoretools import *
import configparser
import re
from collections import defaultdict
from IPy import IP
import pprint
import redis
import json

# 从ASR9K、MX960上拿到相关的策略路由
# # 9K上需要拿的表
# - SheQu(非10地址需要)
# - SheQu-From-9K3-4(10地址和非10地址都需要)
# # MX960是需要的表
# - SheQu10NAT(非10地址需要)
# - HWNAT-OUTSIDE(10地址需要)


def getPBRFromASR9K(asr9k):
    dic_CORE_COMMAND = {
        "9k": ['terminal length 0', 'show running-config ipv4 access-list SheQu', 'show running-config ipv4 access-list SheQu-From-9K3-4', 'exit'],
        "mx960": ['show configuration firewall | no-more', 'quit']
    }

    dic_REGEXP = {
        'CC9KWH1': r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.142)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.146)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.150)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.154)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.166)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.17.220)',
        'CC9KWH2': r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.2.142)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.2.146)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.2.150)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.2.154)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.2.166)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.17.220)',
        'CC960WH3': r'source-address[\S\s]*?}[\S\s]*?}[\S\s]*?}',
        'CC960WH4': r'source-address[\S\s]*?}[\S\s]*?}[\S\s]*?}'
    }

    CC9K_HSmap2PA = {
        '10.207.1.142': 'LJSHS-1_PA76',
        '10.207.1.146': 'LJSHS-1_PA70',
        '10.207.1.150': 'LJSHS-2_PA73',
        '10.207.1.154': 'LJSHS-2_PA69',
        '10.207.1.166': 'LJSHS-4_PA71',
        '10.207.2.146': 'LJSHS-1_PA70',
        '10.207.2.142': 'LJSHS-1_PA76',
        '10.207.2.150': 'LJSHS-2_PA73',
        '10.207.2.154': 'LJSHS-2_PA69',
        '10.207.2.166': 'LJSHS-4_PA71',
        '10.207.17.220': 'GameVip_PAx'
    }

    asr9k_pbr = {
        'shequ': [],
        'shequ-from-9k34': []
    }

    coreid = asr9k
    config = configparser.ConfigParser()
    config.read(r'/var/www/html/cgi-bin/core.conf', encoding='utf-8')

    style = config.get(coreid, 'style')
    ip = config.get(coreid, 'ip')
    loginName = config.get(coreid, 'loginName')
    loginPassword = config.get(coreid, 'loginPassword')
    regexp4pbr = dic_REGEXP[coreid]
    cmd_list = dic_CORE_COMMAND[style]

    # 处理ASR9K上的PBR
    rawinfo = GetRawInfo(ip, loginName, loginPassword, cmd_list, r'[$#>]')
    # print(rawinfo)

    # 拿到PBR:SheQu
    regexp = r'(ipv4 access-list SheQu[^-][\s\S]*?!)'
    pbr_shequ_segment = re.findall(regexp, rawinfo)
    # print(pbr_shequ_segment)
    # 开始处理shequ策略内容
    # regexp = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.142)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.146)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.150)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.154)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.166)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.17.220)'
    pbrinfo = re.findall(regexp4pbr, pbr_shequ_segment[0])
    CC9KWH_SheQu = []
    for pool_segment in pbrinfo:
        ip, mask, key4hs = [item for item in pool_segment if item]
        # 根据ip 反掩码, 返回网络地址
        # mask = '.'.join([str(255 - int(item)) for item in mask.split('.')])
        network = IP(ip).make_net(
            '.'.join([str(255 - int(item)) for item in mask.split('.')])).strNormal()
        # print(network, CC9K_HSmap2PA[key4hs])
        CC9KWH_SheQu.append({network: CC9K_HSmap2PA[key4hs]})

    # pprint.pprint(CC9KWH_SheQu, indent=2)
    asr9k_pbr['shequ'].extend(CC9KWH_SheQu)

    # 拿到PBR:SheQu-From-9K3-4
    regexp = r'(ipv4 access-list SheQu[-][\s\S]*?!)'
    pbr_shequFrom9k34_segment = re.findall(regexp, rawinfo)
    # 开始处理SheQu-From-9K3-4策略内容
    # regexp = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.142)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.146)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.150)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.154)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.1.166)|(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).+(?<!nexthop2 ipv4 )(10.207.17.220)'
    pbrinfo = re.findall(regexp4pbr, pbr_shequFrom9k34_segment[0])
    CC9KWH_SheQu_From_9K34 = []
    for pool_segment in pbrinfo:
        ip, mask, key4hs = [item for item in pool_segment if item]
        # 根据ip 反掩码, 返回网络地址
        # mask = '.'.join([str(255 - int(item)) for item in mask.split('.')])
        network = IP(ip).make_net(
            '.'.join([str(255 - int(item)) for item in mask.split('.')])).strNormal()
        # print(network, CC9K_HSmap2PA[key4hs])
        CC9KWH_SheQu_From_9K34.append({network: CC9K_HSmap2PA[key4hs]})
    # print(pbr_SheQuFrom9K3_4_segment)
    asr9k_pbr['shequ-from-9k34'].extend(CC9KWH_SheQu_From_9K34)

    return asr9k_pbr


def getPBRFromMX960(mx960):
    dic_CORE_COMMAND = {
        "mx960": ['show configuration firewall | no-more', 'quit']
    }

    dic_REGEXP = {
        'CC960WH3': r'source-address[\S\s]*?}[\S\s]*?}[\S\s]*?}',
        'CC960WH4': r'source-address[\S\s]*?}[\S\s]*?}[\S\s]*?}'
    }

    MX960_HSmap2PA = {
        'Nexthop_CQ_HS': 'CQHS-1_PA79',
        'Nexthop_CQ_HS_1_1': 'CQHS-1_PA79',
        'Nexthop_CQ_HS_2': 'CQHS-2_PA80',
        'Nexthop_CQ_HS_2_1': 'CQHS-2_PA80',
        'Nexthop_CQ_HS_3': 'CQHS-3_PA68',
        'Nexthop_CQ_HS_3_1': 'CQHS-3_PA68',
        'Nexthop_CQ_HS_32': 'CQHS-3_PA78'
    }

    mx960_pbr = {
        'shequ10nat': [],
        'hwnat-outside': []
    }

    coreid = mx960
    config = configparser.ConfigParser()
    config.read(r'/var/www/html/cgi-bin/core.conf', encoding='utf-8')

    style = config.get(coreid, 'style')
    ip = config.get(coreid, 'ip')
    loginName = config.get(coreid, 'loginName')
    loginPassword = config.get(coreid, 'loginPassword')
    regexp4pbr = dic_REGEXP[coreid]
    cmd_list = dic_CORE_COMMAND[style]

    # 处理MX960上的PBR
    rawinfo = GetRawInfo(ip, loginName, loginPassword, cmd_list, r'[$>]')
    # print(rawinfo)

    # 拿到PBR:SheQu10NAT
    regexp = r'(filter SheQu10NAT[\S\s]*?filter)'
    pbr_shequ10nat_segment = re.findall(regexp, rawinfo)
    # pprint.pprint(pbr_shequ10nat_segment[0])
    # 开始处理shequ10nat策略内容
    pbrinfo = re.findall(regexp4pbr, pbr_shequ10nat_segment[0])
    MX960_SheQu10NAT = []
    for pool_segment in pbrinfo:
        needNextStep = re.search(r'routing-instance (.+);', pool_segment)
        if needNextStep:
            # print(needNextStep.group(1))
            routing_name = needNextStep.group(1)
            pools = re.findall(
                r'(\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\/\d{1,})', pool_segment)
            for pool in pools:
                # print(f'  {pool}')
                if MX960_HSmap2PA.__contains__(routing_name):
                    # print(f'{pool}:  {routing_name}')
                    MX960_SheQu10NAT.append(
                        {pool: MX960_HSmap2PA[routing_name]})

    # pprint.pprint(MX960_SheQu10NAT, indent=2)
    mx960_pbr['shequ10nat'].extend(MX960_SheQu10NAT)

    # 拿到PBR:HWNAT-OUTSIDE
    regexp = r'(filter HWNAT-OUTSIDE[\S\s]*?filter)'
    pbr_hwnat_outside_segment = re.findall(regexp, rawinfo)
    # pprint.pprint(pbr_hwnat_outside_segment[0])
    # 开始处理hwnat_outside策略内容
    pbrinfo = re.findall(regexp4pbr, pbr_hwnat_outside_segment[0])
    MX960_HWNAT_OUTSIDE = []
    for pool_segment in pbrinfo:
        needNextStep = re.search(r'routing-instance (.+);', pool_segment)
        if needNextStep:
            # print(needNextStep.group(1))
            routing_name = needNextStep.group(1)
            pools = re.findall(
                r'(\d{1,}\.\d{1,}\.\d{1,}\.\d{1,}\/\d{1,})', pool_segment)
            for pool in pools:
                # print(f'  {pool}')
                if MX960_HSmap2PA.__contains__(routing_name):
                    # print(f'{pool}:  {routing_name}')
                    MX960_HWNAT_OUTSIDE.append(
                        {pool: MX960_HSmap2PA[routing_name]})

    # pprint.pprint(MX960_HWNAT_OUTSIDE, indent=2)
    mx960_pbr['hwnat-outside'] = MX960_HWNAT_OUTSIDE

    return mx960_pbr


if __name__ == '__main__':
    asr9k1_pbr = getPBRFromASR9K('CC9KWH1')
    asr9k2_pbr = getPBRFromASR9K('CC9KWH2')
    # pprint.pprint(asr9k2_pbr, indent=2)

    mx9603_pbr = getPBRFromMX960('CC960WH3')
    mx9604_pbr = getPBRFromMX960('CC960WH4')
    # pprint.pprint(mx9604_pbr, indent=2)

    # 打开文件准备写入
    filename = f'/var/www/html/pbr_asr9k1.json'
    with open(filename, "w") as f:
        f.write(json.dumps(asr9k1_pbr, indent=2))

    filename = f'/var/www/html/pbr_asr9k2.json'
    with open(filename, "w") as f:
        f.write(json.dumps(asr9k2_pbr, indent=2))

    filename = f'/var/www/html/pbr_mx9603.json'
    with open(filename, "w") as f:
        f.write(json.dumps(mx9603_pbr, indent=2))

    filename = f'/var/www/html/pbr_mx9604.json'
    with open(filename, "w") as f:
        f.write(json.dumps(mx9604_pbr, indent=2))

    # 写入redis
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    r.set(f'pbr_asr9k1', json.dumps(asr9k1_pbr))
    r.set(f'pbr_asr9k2', json.dumps(asr9k2_pbr))
    r.set(f'pbr_mx9603', json.dumps(mx9603_pbr))
    r.set(f'pbr_mx9604', json.dumps(mx9603_pbr))
