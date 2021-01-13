#!/usr/bin/env python
# coding:utf8
from fastapi import FastAPI
import requests
import re
from collections import defaultdict
import json
import redis
from tools4main import *

app = FastAPI()


def getNasportID(username):
    soap_url = r'http://10.207.18.171/WHFaultServiceV2/WebService.asmx'
    headers = {'Content-Type': 'application/soap+xml; charset=utf-8'}
    params = f'<?xml version="1.0" encoding="utf-8"?><soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"><soap12:Body><GetUserQINQ xmlns="http://tempuri.org/"><userid>{username}</userid></GetUserQINQ></soap12:Body></soap12:Envelope>'
    resp = requests.request(
        'POST', soap_url, headers=headers, data=params.encode())
    result = re.search(
        r'\<GetUserQINQResult\>(\S+)<\/GetUserQINQResult', resp.text)

    if result:
        return result.group(1)
    else:
        return ''


@app.get("/username/{username}")
async def username(username: str):
    # regexp_nasportid = r'value=\"(.+)\" id.+Label1\"\>(.+)\<\/span'

    # url = "http://211.161.158.146/userfindnasportid/Default.aspx"
    # payload = {"__VIEWSTATE": "/wEPDwUKMTAxNjU2Mjk3OQ9kFgICAw9kFgYCDw88KwARAQAPFgIeB1Zpc2libGVoZGQCEQ8PFgIeBFRleHQFEuS/oeaBr+afpeivouS4jeWIsGRkAhgPPCsAEQBkGAIFCUdyaWRWaWV3Mg9nZAUJR3JpZFZpZXcxD2dkH5774PfOsrEdwymqd/pQC7iA0yzqisFm5mLQcbGnLNk=",
    #            "__VIEWSTATEGENERATOR": "F7F31A72", "__EVENTVALIDATION": "/wEWCALNob/BDQLs0bLrBgKM54rGBgLs0fbZDALs0Yq1BQK7q7GGCALs0e58AtaUz5sC+rXm+hAeBOlcqHO1yLMAoEPWZ+MKDKaKHTxGUpMrfFE=", "TextBox1": "", "Button1": "查找", "TextBox2": "", "TextBox3": "", "TextBox4": ""}
    # payload['TextBox1'] = username
    # res = requests.post(url=url, data=payload)
    # # print(res.text)
    # result_res = re.findall(regexp_nasportid, res.text)
    # username = result_res[0][0]
    # # print(result_res)

    # 传入的是ip，先查到用户帐号
    # getUsername函数返回一个对象，ip无效：{用户帐号为空+xxx}；不在线：{用户帐号为空+穿越的nat设备}；在线：{用户帐号+xxx}；
    if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', username):
        dic_username = getUsername(username)
    else:
        # 直接给出的是一个帐号
        dic_username = {
            'success': True,
            'info': {
                'username': username
            }
        }

    # 如果根据ip查到的用户帐号为空：{ip无效:false|用户不在线:false|用户在线:true}
    if not dic_username['success']:
        return json.dumps(dic_username)

    # # 到这里，表示用户在线或是需要查询给出的帐号信息
    # # soap_nasportid = getNasportID(username)
    username = dic_username['info']['username']
    # soap_nasportid = getNasportID(dic_username['info']['username'])
    soap_nasportid = getNasportID(username)
    result = defaultdict(lambda: {})
    try:
        # brasname, brasport, pevlan, cevlan = result_res[0][1].split(':')
        # nasportid = brasname + ":" + brasport
        # brasname, brasport, pevlan, cevlan = result_res[0][1].split(':')
        brasname, brasport, pevlan, cevlan = soap_nasportid.split(':')
        nasportid = f'{brasname}:{brasport}'

        # 这里成功拿到了nasportid，可以向特定bras发起查询，以获取在线用户的ip地址和产品属性
        dic_UserIpQos = getUserIpInfo(username, brasname)

        # 根据nasportid，在redis中查询对应的olt列表
        r = redis.Redis(host='127.0.0.1', port=6379, db=0)
        oltips = json.loads(r.get(nasportid).decode('utf-8'))

        # 包含指定nasportid的olt，应该只有一台
        result_olt = defaultdict(lambda: {})
        for ip in oltips:
            # print(ip)
            vlan2pon = json.loads(r.get(ip).decode('utf-8'))
            # print(vlan2pon)
            # 查看该olt中，是否包含有指定的外层vlan
            pons = vlan2pon.get(pevlan, False)
            # print(ip, pons)
            if bool(pons):
                # 有指定的外层vlan，将oltip存储到result_olt列表中
                result_olt[ip]['pon'] = pons
                result_olt[ip]['name'] = vlan2pon['name']
                result_olt[ip]['type'] = vlan2pon['type']
                # print(result_olt)
        # 正常情况下，应该只有一台olt的信息被查询到
        if len(result_olt) == 1:
            for ip, olt in result_olt.items():
                # 如果不是泰龙的olt
                if olt['type'] != 'tailong':
                    result["success"] = True
                    result["info"]["username"] = username
                    result["info"]["nasportid"] = nasportid
                    result["info"]["pevlan"] = pevlan
                    result["info"]["cevlan"] = cevlan
                    result["info"]["oltname"] = olt["name"]
                    result["info"]["oltip"] = ip
                    result["info"]["pon"] = olt["pon"]
                    result["info"]["onu"] = '-'
                    result["info"]["hillstone"] = '-'
                    result["info"]["panabit"] = '-'
                    result["info"]["detail"] = olt['type']
                    # 是raisecom或是greenway下的用户
                    # 如果pon信息中只有唯一的一个pon口，直接返回数据
                    if len(olt["pon"]) == 1:
                        result["info"]["pon"] = olt["pon"][0]
                        # 定位具体onu
                        if int(cevlan) < 1001:
                            # iptv用户，或是非武汉地区用户
                            result["success"] = True
                            result["info"]["detail"] = f"无法定位"
                        elif int(cevlan) < 2537:
                            result["info"]["onu"] = f'{olt["pon"][0]}/{int((int(cevlan) - 1000) / 24) + 1}'
                        else:
                            result["info"]["onu"] = f'{olt["pon"][0]}/{int((int(cevlan) - 2536) / 24) + 1}'

                    elif len(olt["pon"]) == 2:
                        # 需要根据内层vlan来确定是哪个pon口
                        pon1 = olt["pon"][0]
                        pon2 = olt["pon"][1]
                        pon_odd = f"{pon1.split('/')[0]}/{min(int(pon1.split('/')[1]), int(pon2.split('/')[1]))}"
                        pon_even = f"{pon1.split('/')[0]}/{max(int(pon1.split('/')[1]), int(pon2.split('/')[1]))}"
                        # 确定pon口，并定位onu
                        if int(cevlan) < 1001:
                            # iptv用户，或是非武汉地区用户
                            result["success"] = False
                            result["info"]["detail"] = f"无法定位"
                        elif int(cevlan) < 2537:
                            # 内层vlan小2537，为奇数pon口
                            result["info"]["pon"] = pon_odd
                            result["info"]["onu"] = f'{pon_odd}/{int((int(cevlan) - 1000) / 24) + 1}'
                        else:
                            # 内层>2536，为偶数pon口
                            result["info"]["pon"] = pon_even
                            result["info"]["onu"] = f'{pon_even}/{int((int(cevlan) - 2536) / 24) + 1}'
                    else:
                        # pon口数 > 2，无法确定是哪个pon口下，哪个onu
                        result["success"] = False
                        result["info"]["detail"] = f"外层vlan{pevlan}对应多个pon口，无法确定为哪个pon口"

                    result['info'].update(dic_UserIpQos)
                    # print(json.dumps(result, indent=2))
                    # print(
                    #     f'外层vlan:{pevlan}包含在 {olt["name"]}({ip}) 中，pon口是:{olt["pon"]}')
                else:
                    # 是泰龙是olt，只显示olt名称和ip，不显示具体pon口信息和onu信息
                    result["success"] = True
                    result["info"]["username"] = username
                    result["info"]["nasportid"] = nasportid
                    result["info"]["pevlan"] = pevlan
                    result["info"]["cevlan"] = cevlan
                    result["info"]["oltname"] = olt["name"]
                    result["info"]["oltip"] = ip
                    result["info"]["pon"] = '-'
                    result["info"]["onu"] = '-'
                    result["info"]["hillstone"] = '-'
                    result["info"]["panabit"] = '-'
                    result["info"]["detail"] = 'tailong'

                    result['info'].update(dic_UserIpQos)
                    # print(json.dumps(result, indent=2))
                    # print(f'外层vlan: {pevlan}包含在 {olt["name"]}({ip}) 中')
        elif len(result_olt) == 0:
            result["success"] = False
            result["info"]["username"] = username
            result["info"]["nasportid"] = nasportid
            result["info"]["pevlan"] = pevlan
            result["info"]["cevlan"] = cevlan
            result["info"]["oltname"] = '-'
            result["info"]["oltip"] = '-'
            result["info"]["pon"] = '-'
            result["info"]["onu"] = '-'
            result["info"]["hillstone"] = '-'
            result["info"]["panabit"] = '-'
            result["info"]["detail"] = f'指定的外层vlan:{pevlan}没有在olt中被找到'

            result['info'].update(dic_UserIpQos)
            # print(json.dumps(result, indent=2))
            # print(f'没有找到指定的vlan：{pevlan}')
        else:
            result["success"] = False
            result["info"]["username"] = username
            result["info"]["nasportid"] = nasportid
            result["info"]["pevlan"] = pevlan
            result["info"]["cevlan"] = cevlan
            result["info"]["oltname"] = '-'
            result["info"]["oltip"] = result_olt
            result["info"]["pon"] = '-'
            result["info"]["onu"] = '-'
            result["info"]["hillstone"] = '-'
            result["info"]["panabit"] = '-'
            result["info"]["detail"] = f'指定的外层vlan在多个olt中被找到:{[{key:value["name"]} for key, value in result_olt.items()]}'

            result['info'].update(dic_UserIpQos)
            # print(json.dumps(result, indent=2))
            # print(f'查询到了多台olt：{result_olt}包含外层vlan，这里有bug')

        return json.dumps(result)
    except AttributeError:
        # 没有在redis中查找到nasportid，很可能是高校用户
        result["success"] = False
        result["info"]["username"] = username
        result["info"]["nasportid"] = nasportid
        result["info"]["pevlan"] = pevlan
        result["info"]["cevlan"] = cevlan
        result["info"]["oltname"] = '-'
        result["info"]["oltip"] = '-'
        result["info"]["pon"] = '-'
        result["info"]["onu"] = '-'
        result["info"]["hillstone"] = '-'
        result["info"]["panabit"] = '-'
        result["info"]["detail"] = '高校Bras或是已下线Bras？请核查'
        result["info"]["interface"] = '-'
        result["info"]["userip"] = '-'
        result["info"]["qos"] = '-'
        result["info"]["brasname"] = nasportid.split(':')[0]
        result["info"]["brasip"] = '-'
        result["info"]['pool'] = '-'
        # print(json.dumps(result, indent=2))
        return json.dumps(result)
    except ValueError:
        # 网页没有查到用户的nasportid
        # print(username, result_res[0][1])
        result["success"] = False
        result["info"]["username"] = username
        result["info"]["nasportid"] = '-'
        result["info"]["pevlan"] = '-'
        result["info"]["cevlan"] = '-'
        result["info"]["oltname"] = '-'
        result["info"]["oltip"] = '-'
        result["info"]["pon"] = '-'
        result["info"]["onu"] = '-'
        result["info"]["hillstone"] = '-'
        result["info"]["panabit"] = '-'
        result["info"]["detail"] = "未查询到信息"
        result["info"]["interface"] = '-'
        result["info"]["userip"] = '-'
        result["info"]["qos"] = '-'
        result["info"]["brasname"] = '-'
        result["info"]["brasip"] = '-'
        result["info"]['pool'] = '-'
        # print(json.dumps(result, indent=2))
        return json.dumps(result)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
