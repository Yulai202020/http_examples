import math, signal, sys, threading, json
from socket import *
from urllib.parse import unquote, parse_qs

functions = {}
templates_dir = "templates/"
server = socket(AF_INET, SOCK_STREAM)

def read_file(file):
    with open(file) as f:
        return f.read()

def bind(function, link):
    functions[link] = function

def exit_handler(signum, frame):
    print()
    print("Exiting, stoping server.")
    server.close()
    sys.exit(0)

def start_thread(conn, addr):
    def find_last_occurrence(lst, value):
        indices = [i for i, x in enumerate(lst) if x == value]
        return indices[-1] if indices else -1

    splited_request = []
    is_POST = False
    is_GET = False
    link = ''
    headers = {}
    posted_json = {}

    while True:
        # reading
        message = ''
        
        data = conn.recv(4096)
        if not data:
            break

        message += data.decode()

        # split
        splited_request = message.split("\n")
        id_of_start_read = find_last_occurrence(splited_request, "\r")
        tmp = splited_request[1:id_of_start_read]

        for i in tmp:
            i = i[:-1]
            i = i.split(": ")
            headers[i[0]] = ": ".join(i[1:])

        # its simple
        if splited_request[0].startswith("GET") and "\r\n\r\n" in message:
            is_GET = True
            break

        elif splited_request[0].startswith("POST") and "\r\n\r\n" in message:
            lenght_of_content = 0

            for i in splited_request:
                if i.startswith("Content-Length: "):
                    lenght_of_content = int(i[16:-1])

            read = "\n".join(splited_request[id_of_start_read+1:])

            if len(read) != lenght_of_content:
                html = read_file(templates_dir + "invalid_json_length.html")
                conn.sendall(b"HTTP/1.0 400 OK\r\n\r\n" + html.encode())

                conn.close()
                return

            is_POST = True
            break

    for i in splited_request:
        if i.startswith("GET "):
            link = i[4:-10]
        elif i.startswith("POST "):
            link = i[5:-10]

    if is_POST:
        for i in splited_request:
            if i.startswith("Content-Type: ") :
                if i[14:31] == "application/json\r":
                    try:
                        posted_json = json.loads("\n".join(splited_request[splited_request.index("\r"):]))
                    except:
                        html = read_file(templates_dir + "json_format_error.html")
                        conn.sendall(b"HTTP/1.0 400 OK\r\n\r\n" + html.encode())
                        conn.close()
                        return
             
                elif i[14:48] == "application/x-www-form-urlencoded\r":
                    index = find_last_occurrence(splited_request, "\r")

                    data = "\n".join(splited_request[index+1:])
                    parsed_query = parse_qs(data)

                    posted_json = {key: value[0] for key, value in parsed_query.items()}

                else:
                    html = read_file(templates_dir + "no_json_error.html")
                    conn.sendall(b"HTTP/1.0 400 OK\r\n\r\n" + html.encode())        
                    conn.close()
                    return

        try:
            msg = functions[link](posted_json)
            conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
        except:
            html = read_file(templates_dir + "404.html")
            conn.sendall(b"HTTP/1.0 404 OK\r\n\r\n" + html.encode())        

    elif link.find("?") != -1:
        # parse link
        link = unquote(link)

        # get data to dict
        id_of_start_read = link.find("?") + 1

        data = link[id_of_start_read:]
        parsed_query = parse_qs(data)
        result = {key: value[0] for key, value in parsed_query.items()}

        # get link
        link = link[:id_of_start_read-1]

        try:
            msg = functions[link[:id_of_start_read-1]](result)
            conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
        except:
            html = read_file(templates_dir + "404.html")
            conn.sendall(b"HTTP/1.0 404 OK\r\n\r\n" + html.encode())

    else:
        try:
            msg = functions[link]()
            conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
        except:
            html = read_file(templates_dir + "404.html")
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