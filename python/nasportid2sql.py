#!/usr/bin/env python
# coding:utf8
import urllib.request
import json
import pymssql

if __name__ == '__main__':
    # 这里从192.168.108.102上提取oltnasportid.json信息
    url = "http://192.168.108.102:8983/oltnasportid.json"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    data = resp.read().decode('utf-8')
    olts = json.loads(data)
    # print(olts)

    # 按类型，分为{raisecom, greenway, tailong}
    _olt_raisecom = [{ip: olts[ip]}
                     for ip in olts if olts[ip]['type'] == 'raisecom']
    olt_raisecom = {}
    for item in _olt_raisecom:
        olt_raisecom.update(item)

    _olt_greenway = [{ip: olts[ip]}
                     for ip in olts if olts[ip]['type'] == 'greenway']
    olt_greenway = {}
    for item in _olt_greenway:
        olt_greenway.update(item)

    _olt_tailong = [{ip: olts[ip]}
                    for ip in olts if olts[ip]['type'] == 'tailong']
    olt_tailong = {}
    for item in _olt_tailong:
        olt_tailong.update(item)

    # print(len(olt_greenway))
    # print(len(olt_raisecom))
    # print(len(olt_tailong))

    # sql服务器名，这里(127.0.0.1)是本地数据库IP
    serverName = '124.202.158.179'
    # 登陆用户名和密码
    userName = 'oltlist'
    passWord = 'oltlist!@#123'
    # 建立连接并获取cursor
    conn = pymssql.connect(serverName, userName, passWord, "radiustools")
    cursor = conn.cursor()

    # 清空表
    cursor.execute("DELETE FROM oltlist_all")
    conn.commit()

    # 添加raisecom的数据
    for key, value in olt_raisecom.items():
        olt_ip = key
        olt_name = value['name']
        olt_vlan = value['vlan']
        olt_domain = value['domain']
        olt_type = value['type']
        olt_nastportid = ';'.join(value['nasportid'])
        #print(olt_ip, olt_name, olt_nastportid, olt_domain, olt_vlan, olt_type)
        sqlstr = f"INSERT INTO oltlist_all(oltip, oltname, oltvlan, oltbaspon, oltdomain, description) VALUES('{olt_ip}', '{olt_name}', '{olt_vlan}', '{olt_nastportid}', '{olt_domain}', '{olt_type}')"
        # print(sqlstr)
        cursor.execute(sqlstr)

    # 添加greenway的数据
    for key, value in olt_greenway.items():
        olt_ip = key
        olt_name = value['name']
        olt_vlan = value['vlan']
        olt_domain = value['domain']
        olt_type = value['type']
        olt_nastportid = ';'.join(value['nasportid'])
        # print(olt_ip, olt_name, olt_nastportid, olt_domain, olt_vlan, olt_type)
        sqlstr = f"INSERT INTO oltlist_all(oltip, oltname, oltvlan, oltbaspon, oltdomain, description) VALUES('{olt_ip}', '{olt_name}', '{olt_vlan}', '{olt_nastportid}', '{olt_domain}', '{olt_type}')"
        # print(sqlstr)
        cursor.execute(sqlstr)

    conn.commit()
    conn.close()
