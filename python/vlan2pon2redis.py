#!/usr/bin/env python
# coding:utf8
from collections import defaultdict
import urllib.request
import redis
import json

if __name__ == '__main__':
    # 获取raisecom的vlan2pon信息
    url = "http://192.168.108.79:8983/works/raisecom/rcoltvlan2pon.json"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    data = resp.read().decode('utf-8')
    vlan2pon = json.loads(data)

    # 获取greenway的vlan2pon信息
    url = "http://192.168.108.81/works/greenway/gwoltvlan2pon.json"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    data = resp.read().decode('utf-8')
    temp = json.loads(data)

    # 合并后的数据
    vlan2pon.update(temp)

    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    # print(len(vlan2pon))
    for ip, vlans in vlan2pon.items():
        # print(ip, json.dumps(vlans))
        r.set(ip, json.dumps(vlans))
