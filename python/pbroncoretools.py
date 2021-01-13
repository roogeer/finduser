#!/usr/bin/env python
# coding:utf8
import pexpect


def GetRawInfo(ipAddress, loginName, loginPassword, cmd_list, loginprompt):
    #print(ipAddress, loginName, loginPassword, cmd_list)
    # 提示符，可能是’ $ ’ , ‘ # ’或’ > ’
    # loginprompt = '[$>]'
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
                # print(cmd)
                child.sendline(cmd)
                index = child.expect(
                    [loginprompt, pexpect.EOF, pexpect.TIMEOUT])
                if(index == 0):
                    # pass
                    # print('命令行输出的结果：')
                    # print(child.before.decode('utf-8'))
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
