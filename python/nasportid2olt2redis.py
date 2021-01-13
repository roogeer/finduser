#!/usr/bin/env python
# coding:utf8
from collections import defaultdict
import urllib.request
import json
import redis

if __name__ == '__main__':
    # 这里从192.168.108.102上提取oltnasportid.json信息
    url = "http://192.168.108.102:8983/oltnasportid.json"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    data = resp.read().decode('utf-8')
    olts = json.loads(data)
    # print(type(olts))

    # 根据nasportid，将olt归类
    nasportid = defaultdict(list)
    for ip, value in olts.items():
        # print(ip, type(value))
        for id in value['nasportid']:
            # print(id)
            nasportid[id].append(ip)

    # print(len(nasportid))

    # 将数据写入redis
    r = redis.Redis(host='127.0.0.1', port=6379, db=0)
    for key, value in nasportid.items():
        r.set(key, json.dumps(value))
        # print(key, value)
