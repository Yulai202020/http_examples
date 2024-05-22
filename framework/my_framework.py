import math, signal, sys, threading, json
from socket import *

functions = {}
server = socket(AF_INET, SOCK_STREAM)

def bind(function, link):
    functions[link] = function

def exit_handler(signum, frame):
    print()
    print("Exiting, stoping server.")
    server.close()
    sys.exit(0)

def start_thread(conn, addr):
    message = b''

    while True:
        data = conn.recv(4096)
        if not data:
            break
        message += data
    
    message = message.decode()
    print(message)
    
    splited_request = message.split("\n")

    is_POST = splited_request[0].startswith("POST")
    is_GET = splited_request[0].startswith("GET")
    link = ''
    posted_json = ''

    if is_GET:
        for i in splited_request:
            if i.startswith("GET "):
                link = i[4:-10]

    elif is_POST:
        for i in splited_request:
            if i.startswith("Content-Type: ") and i[14:] == "application/json":
                posted_json = json.loads(splited_request[splited_request.index("\n"):])
            else:
                with open("400.html") as f:
                    html = f.read()
                    conn.sendall(b"HTTP/1.0 400 OK\r\n\r\n" + html.encode())        

    if is_POST:
        try:
            msg = functions[link](posted_json)
            conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
        except:
            with open("404.html") as f:
                html = f.read()
                conn.sendall(b"HTTP/1.0 404 OK\r\n\r\n" + html.encode())        

    elif link.find("?") != -1:
        args = link[link.find("?")+1:]
        args = args.split("&")
        link = link[0:link.find("?")]

        getted_dict = {}

        for i in args:
            i = i.split("=")
            getted_dict[i[0]] = i[1]

        try:
            msg = functions[link](getted_dict)
            conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
        except:
            with open("404.html") as f:
                html = f.read()
                conn.sendall(b"HTTP/1.0 404 OK\r\n\r\n" + html.encode())

    else:
        try:
            msg = functions[link]()
            conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
        except:
            with open("404.html") as f:
                html = f.read()
                conn.sendall(b"HTTP/1.0 404 OK\r\n\r\n" + html.encode())

    conn.close()

def start_server(host, port):
    HOST = (host, port)

    server.bind(HOST)
    server.listen()

    signal.signal(signal.SIGINT, exit_handler)

    while True:
        conn, addr = server.accept()

        t = threading.Thread(target = start_thread, args = (conn, addr))
        t.start()
    
    server.close()