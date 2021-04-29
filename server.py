#!/usr/bin/env python3
import socket
import os
import sys
import signal
import hashlib


def readAllData(data, f):
    dic = {}
    while data != "\n":
        head, content = parseData(data)
        dic[head] = content
        data = f.readline().decode('UTF-8')
    return dic


def parseData(parse):
    flag = 0
    stripLine = parse.strip()
    if not stripLine.isascii():
        flag += 1
    try:
        stripLine = stripLine.strip().split(":")
    except:
        flag += 1
    if len(stripLine) != 2 or stripLine[0].find("/") != -1:
        flag += 1
    if flag == 0:
        return stripLine[0], stripLine[1]
    else:
        return "", ""


def dicControl(dic):
    if len(dic) > 2:
        return 200, 'Bad request'
    for header in dic:
        if header == "" or dicHeaders[header] == "":
            return 200, 'Bad request'
    return 100, 'OK'


def readMethod(dic):
    code, msg, reply, header = (100, "OK", "", "")
    try:
        with open(f'{dic["Mailbox"]}/{dic["Message"]}') as message_file:
            reply = message_file.read()
            length = len(reply)
            header = (f'Content-length:{length}\n')
    except KeyError:
        code, msg = (200, 'Bad request')
    except FileNotFoundError:
        code, msg = (201, 'No such message')
    except OSError:
        code, msg = (202, 'Read error')
    return code, msg, reply, header


def lsMethod(dic):
    code, msg, reply, header = (100, "OK", "", "")
    try:
        atr_content = os.listdir(dic["Mailbox"])
        atr_length = len(atr_content)
        header = (f'Number-of-messages:{atr_length}\n')
        reply = "\n".join(atr_content) + "\n"
    except KeyError:
        code, msg = (200, 'Bad request')
    except FileNotFoundError:
        code, msg = (203, 'No such mailbox')
    return code, msg, reply, header


def writeMethod(dic, opened_file):
    code, msg, reply, header = (100, "OK", "", "")
    try:
        rep_content = opened_file.read(int(dic["Content-length"]))
        name_content = hashlib.md5(rep_content).hexdigest()
        with open(f'{dic["Mailbox"]}/{name_content}', "w") as message_file:
            message_file.write(rep_content.decode('UTF-8'))
    except KeyError:
        code, msg = (200, 'Bad request')
    except ValueError:
        code, msg = (200, 'Bad request')
    except FileNotFoundError:
        code, msg = (203, 'No such mailbox')
    return code, msg, reply, header


def selectingMethod(meth, dic, opened_file):
    if meth == 'READ':
        return readMethod(dic)
    elif meth == 'LS':
        return lsMethod(dic)
    elif meth == 'WRITE':
        return writeMethod(dic, opened_file)
    else:
        statCode, statMsg = (204, 'Unknown method')
        f.write(f'{statCode} {statMsg}\n'.encode("UTF-8"))
        f.write('\n'.encode('UTF-8'))
        f.flush()
        sys.exit(0)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 9999))
signal.signal(signal.SIGCHLD, signal.SIG_IGN)
s.listen(5)

while True:
    connected_socket, address = s.accept()
    print(f'connection to {address}')
    pid_chld = os.fork()
    if pid_chld == 0:
        s.close()
        f = connected_socket.makefile('rwb')
        while True:
            conHeader, conReply, dicHeaders = ("", "", {})
            method = f.readline().decode('UTF-8').strip()
            if not method:
                break
            data = f.readline().decode('UTF-8')
            dicHeaders = readAllData(data, f)
            statCode, status_msg = dicControl(dicHeaders)

            if statCode == 100:
                print("method: ", method)
                statCode, statMsg, conReply, conHeader = selectingMethod(method, dicHeaders, f)

            f.write(f'{statCode} {status_msg}\n'.encode("UTF-8"))
            f.write(conHeader.encode('UTF-8'))
            f.write('\n'.encode('UTF-8'))
            f.write(conReply.encode('UTF-8'))
            f.flush()
        print(f'{address} closes connection')
        f.close()
        sys.exit(0)
    else:
        connected_socket.close()
