#!/usr/bin/env python
# coding:utf8
import re


class OLT:
    def __init__(self, ip, name, fullPortName):
        # 初始化实例属性
        # ip: olt的ip
        # name: olt的名称
        # fullPortName: olt在bras上的完整端口名称
        self.ip = ip
        self.name = name
        self.fullPortName = fullPortName
        # olt的nasportid信息
        self.nasportid = []

    @property
    def IP(self):
        return self.ip

    @property
    def Name(self):
        return self.name

    @property
    def FullPortName(self):
        if "GE" in self.fullPortName:
            return self.fullPortName.replace('GE', 'Gi')
        else:
            return self.fullPortName

    @property
    def NasportID(self):
        return self.nasportid

    @property
    def Nasport(self):
        regexp = re.compile(r'(.+\d{1,})\.')
        port = regexp.findall(self.fullPortName)
        return port[0]


if __name__ == '__main__':
    testolt = OLT('192.168.0.1', '测试olt', 'GE5/0/5.103')
    print(testolt.IP, testolt.Name, testolt.FullPortName, testolt.Nasport)
