#!/usr/bin/env python
# coding:utf8
import redis
import json
from IPy import IP
import pprint


def getipin_HWNATOUTSIDE(userip, pbr_mx960):
    pbr = pbr_mx960['hwnat-outside']
    for item in pbr:
        for ip, nat in item.items():
            if IP(userip).overlaps(ip) != 0:
                return nat


def getipin_SheQuFrom9K34(userip, pbr_asr9k):
    pbr = pbr_asr9k['shequ-from-9k34']
    for item in pbr:
        for ip, nat in item.items():
            if IP(userip).overlaps(ip) != 0:
                return nat


def getipin_SheQu(userip, pbr_asr9k):
    pbr = pbr_asr9k['shequ']
    for item in pbr:
        for ip, nat in item.items():
            if IP(userip).overlaps(ip) != 0:
                return nat


def getipin_SheQu10NAT(userip, pbr_mx960):
    pbr = pbr_mx960['shequ10nat']
    for item in pbr:
        for ip, nat in item.items():
            if IP(userip).overlaps(ip) != 0:
                return nat


def getHS_PA(ip, bras):
    brasUpLink = {
        'LJS-ME60-1': 'asr9k',
        'LJS-ME60-2': 'asr9k',
        'LJS-ME60-3': 'asr9k',
        'LJS-ME60-4': 'asr9k',
        'LJS-ME60-5': 'asr9k',
        'LJS-7750-1': 'asr9k',
        'XD-ME60-1': 'asr9k',
        'XD-ME60-2': 'asr9k',
        '116-ME60-1': 'asr9k',
        '116-ME60-2': 'asr9k',
        'CQ-ME60-1': 'mx960',
        'CQ-ME60-2': 'mx960',
        'CQ-ME60-3': 'mx960',
        'CQ-ME60-4': 'mx960',
        'CQ-ME60-5': 'mx960',
        'CQ-ME60-6': 'mx960',
        'CQ-ME60-7': 'mx960',
        'CQ-ME60-9': 'mx960',
        'CQ-ME60-10': 'mx960',
        'CQ-7750-1': 'mx960',
        'HY-ME60-1': 'mx960',
        'HY-ME60-2': 'mx960',
        'JZ-7750-1': 'asr9k',
        'XG-7750-1': 'asr9k',
        'HS-ME60-1': 'asr9k',
        'HS-ME60-2': 'mx960',
        'JZ-Redback': 'asr9k',
        'EZ-Redback': 'asr9k'
    }

    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    pbr_asr9k1 = json.loads(r.get('pbr_asr9k1').decode('utf-8'))
    pbr_asr9k2 = json.loads(r.get('pbr_asr9k2').decode('utf-8'))
    pbr_mx9603 = json.loads(r.get('pbr_mx9603').decode('utf-8'))
    pbr_mx9604 = json.loads(r.get('pbr_mx9604').decode('utf-8'))

    # pprint.pprint(pbr_asr9k1, indent=2)
    # pprint.pprint(pbr_asr9k2, indent=2)
    # pprint.pprint(pbr_mx9603, indent=2)
    # pprint.pprint(pbr_mx9604, indent=2)

    # 如果是10的地址，先在MX960-3、MX960-4的HWNAT-OUTSIDE是查询
    ip_a, ip_b, ip_c, ip_d, = ip.split('.')
    if int(ip_a) == 10:
        # 10地址
        # MX960-3:HWNAT-OUTSIDE中查询
        result = getipin_HWNATOUTSIDE(ip, pbr_mx9603)
        if result:
            return result

        # # MX960-4:HWNAT-OUTSIDE中查询
        result = getipin_HWNATOUTSIDE(ip, pbr_mx9604)
        if result:
            return result

        # ASR9K-1:SheQu-From-9K3-4中查询
        result = getipin_SheQuFrom9K34(ip, pbr_asr9k1)
        if result:
            return result

        # # ASR9K-2:SheQu-From-9K3-4中查询
        result = getipin_SheQuFrom9K34(ip, pbr_asr9k2)
        if result:
            return result

        # 程序到这里，表示10地址没有在所有策略中被查询到，配置有bug
        return 'HS?_PA?'
    else:
        # 非10地址
        # 根据bras判断是去哪台核心查询
        core = brasUpLink[bras]
        if 'asr9k' == core:
            # ASR9K-1:SheQu中查询
            result = getipin_SheQu(ip, pbr_asr9k1)
            if result:
                return result

            # ASR9K-2:SheQu中查询
            result = getipin_SheQu(ip, pbr_asr9k2)
            if result:
                return result

            # 程序到这里，表示非10地址没有在9K:SheQu策略中被查询到，配置有bug
            return 'HS?_PA?'
        else:
            # MX960-3:SheQu10NAT
            result = getipin_SheQu10NAT(ip, pbr_mx9603)
            if result:
                return result

            # # MX960-4:SheQu10NAT
            result = getipin_SheQu10NAT(ip, pbr_mx9604)
            if result:
                return result

            # ASR9K-1:SheQu-From-9K3-4中查询
            result = getipin_SheQuFrom9K34(ip, pbr_asr9k1)
            if result:
                return result

            # # ASR9K-2:SheQu-From-9K3-4中查询
            result = getipin_SheQuFrom9K34(ip, pbr_asr9k2)
            if result:
                return result

            # 程序到这里，表示非10地址没有在9K:SheQu策略中被查询到，配置有bug
            return 'HS?_PA?'


if __name__ == '__main__':
    ip = '192.168.0.1'
    # bras = 'LJS-ME60-1'
    bras = 'CQ-ME60-1'
    print(getHS_PA(ip, bras))
