#!/usr/bin/env python3
import socket
import os
import sys
import signal
import hashlib

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
            conHeader = ""
            conReply = ""
            dicHeaders = {}
            method = f.readline().decode('UTF-8').strip()
            if not method:
                break
            data = f.readline().decode('UTF-8')
            while data != "\n":
                flag = 0
                stripLine = data.strip()
                if not stripLine.isascii():
                    flag += 1
                try:
                    stripLine = stripLine.strip().split(":")
                except:
                    flag += 1
                if len(stripLine) != 2 or stripLine[0].find("/") != -1:
                    flag += 1
                if flag == 0:
                    head = stripLine[0]
                    content = stripLine[1]
                else:
                    head, content = ("", "")
                dicHeaders[head] = content
                data = f.readline().decode('UTF-8')

            if len(dicHeaders) > 2:
                statCode, status_msg = (200, 'Bad request')
            for header in dicHeaders:
                if header == "" or dicHeaders[header] == "":
                    statCode, status_msg = (200, 'Bad request')
            statCode, status_msg = (100, 'OK')
            if statCode == 100:
                print("method: ", method)

                if method == 'READ':
                    statCode, statMsg, conReply, conHeader = (100, "OK", "", "")
                    try:
                        with open(f'{dicHeaders["Mailbox"]}/{dicHeaders["Message"]}') as message_file:
                            conReply = message_file.read()
                            length = len(conReply)
                            conHeader = (f'Content-length {length}\n')
                    except KeyError:
                        statCode, statMsg = (200, 'Bad request')
                    except FileNotFoundError:
                        statCode, statMsg = (201, 'No such message')
                    except OSError:
                        statCode, statMsg = (202, 'Read error')

                elif method == 'LS':
                    statCode, statMsg, conReply, conHeader = (100, "OK", "", "")
                    try:
                        atrContent = os.listdir(dicHeaders["Mailbox"])
                        atrLength = len(atrContent)
                        conHeader = (f'Number-of-messages: {atrLength}\n')
                        conReply = "\n".join(atrContent) + "\n"
                    except KeyError:
                        statCode, statMsg = (200, 'Bad request')
                    except FileNotFoundError:
                        statCode, statMsg = (203, 'No such mailbox')

                elif method == 'WRITE':
                    statCode, statMsg, conReply, conHeader = (100, "OK", "", "")
                    try:
                        repContent = f.read(int(dicHeaders["Content-length"]))
                        nameContent = hashlib.md5(repContent).hexdigest()
                        with open(f'{dicHeaders["Mailbox"]}/{nameContent}', "w") as message_file:
                            message_file.write(repContent.decode('UTF-8'))
                    except KeyError:
                        statCode, statMsg = (200, 'Bad request')
                    except ValueError:
                        statCode, statMsg = (200, 'Bad request')
                    except FileNotFoundError:
                        statCode, statMsg = (203, 'No such mailbox')
                else:
                    statCode, statMsg = (204, 'Unknown method')
                    f.write(f'{statCode} {statMsg}\n'.encode("UTF-8"))
                    f.write('\n'.encode('UTF-8'))
                    f.flush()
                    sys.exit(0)
            f.write(f'{statCode} {statMsg}\n'.encode("UTF-8"))
            f.write(conHeader.encode('UTF-8'))
            f.write('\n'.encode('UTF-8'))
            f.write(conReply.encode('UTF-8'))
            f.flush()
        print(f'{address} closed connection')
        f.close()
        sys.exit(0)
    else:
        connected_socket.close()