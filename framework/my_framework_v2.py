import math, signal, sys, threading, json
from socket import *
from urllib.parse import unquote, parse_qs
import ssl
import traceback
import logging
from queue import Queue

functions = {}
templates_dir = "templates/"

logging_queue = Queue()
logger = logging.getLogger("Server")
server = socket(AF_INET, SOCK_STREAM)

def read_file(file):
    with open(file) as f:
        return f.read()

def bind(function, link):
    if link == "/":
        functions["/favicon.ico"] = function
    functions[link] = function

def exit_handler(signum, frame):
    print()
    print("Exiting, stoping server.")
    server.close()
    sys.exit(0)

def logging_thread(is_logging, logsfile_path):

    if is_logging:
        logging.basicConfig(filename=logsfile_path, encoding='utf-8', level=logging.DEBUG)
    else:
        noop = logging.NullHandler()
        logger.addHandler(noop)

    while True:
        if not logging_queue.empty():
            data = logging_queue.get()

            method = data[0]
            msg = data[1]

            if method == "INFO":
                logger.info(msg)
            elif method == "WARN":
                logger.warning(msg)
            elif method == "ERR":
                logger.error(msg)
            else:
                logger.info("Unknown logging method.")

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

        # get headers
        for i in tmp:
            i = i[:-1]
            i = i.split(": ")
            headers[i[0]] = ": ".join(i[1:])

        # get method
        if splited_request[0].startswith("GET") and "\r\n\r\n" in message:
            is_GET = True
            break

        # post method
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

    # get link
    for i in splited_request:
        if i.startswith("GET "):
            link = i[4:-10]
        elif i.startswith("POST "):
            link = i[5:-10]

    # get posted data
    if is_POST:
        for i in splited_request:
            i = i.split(": ")
            if i[0] == "Content-Type" :
                if i[1][:17] == "application/json\r":
                    try:
                        posted_json = json.loads("\n".join(splited_request[splited_request.index("\r"):]))
                        print(posted_json)
                    except:
                        html = read_file(templates_dir + "json_format_error.html")
                        conn.sendall(b"HTTP/1.0 400 OK\r\n\r\n" + html.encode())
                        conn.close()
                        return
             
                elif i[1][:34] == "application/x-www-form-urlencoded\r":
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
            if link in functions.keys():
                msg = functions[link](posted_json)
                conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
            else:
                html = read_file(templates_dir + "404.html")
                conn.sendall(b"HTTP/1.0 404 OK\r\n\r\n" + html.encode())

        except Exception as err:
            error_exc = traceback.format_exc()
            logging_queue.put(["ERR", error_exc])
            conn.sendall(b"HTTP/1.0 500 Internal Server Error\r\n\r\nServer raised error: " + type(err).__name__.encode())

    # get "get"ted data
    elif link.find("?") != -1:
        # parse link
        link = unquote(link)
        link = link.split("?")

        # get data to dict
        data = link[1]
        parsed_query = parse_qs(data)
        result = {key: value[0] for key, value in parsed_query.items()}

        try:
            if link[0] in functions.keys():
                msg = functions[link[0]](result)
                conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
            else:
                html = read_file(templates_dir + "404.html")
                conn.sendall(b"HTTP/1.0 404 OK\r\n\r\n" + html.encode())

        except Exception as err:
            error_exc = traceback.format_exc()
            logging_queue.put(["ERR", error_exc])
            conn.sendall(b"HTTP/1.0 500 OK\r\n\r\nServer raised error: " + type(err).__name__.encode())

    # if data wasnt uploaded
    else:
        try:
            if link in functions.keys():
                msg = functions[link]()
                conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
            else:
                html = read_file(templates_dir + "404.html")
                conn.sendall(b"HTTP/1.0 404 OK\r\n\r\n" + html.encode())

        except ssl.SSLEOFError as err:
            print("Someone getting own certificate.")

        except Exception as err:
            error_exc = traceback.format_exc()
            logging_queue.put(["ERR", error_exc])
            conn.sendall(b"HTTP/1.0 500 OK\r\n\r\nServer raised error: " + type(err).__name__.encode())

    conn.close()

def start_server(host, port, protocol="http", is_logging=False, logsfile_path=None):
    global server
    # start server
    HOST = (host, port)
    server.bind(HOST)
    server.listen()

    # start logging method
    logging_th = threading.Thread(target=logging_thread, args=(is_logging, logsfile_path, ))
    logging_th.start()

    # setup logging
    logging_queue.put(["INFO", "Starting server."])

    # setup ssl
    if protocol == "https":
        logging_queue.put(["INFO", "Setup certificates."])
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(certfile="cert.pem", keyfile="cert_key.pem")

    # if ^C
    signal.signal(signal.SIGINT, exit_handler)

    while True:
        conn, addr = server.accept()
        # if https encrypt
        if protocol == "https":
            logging_queue.put(["INFO", "Encrypt connection."])
            conn = context.wrap_socket(conn, server_side=True)

        logging_queue.put(["INFO", f"{addr} was connected."])

        # start thread
        t = threading.Thread(target = start_thread, args = (conn, addr))
        t.start()
    
    # close
    server.close()