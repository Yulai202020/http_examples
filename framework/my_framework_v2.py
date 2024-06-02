from socket import *
from queue import Queue
from jinja2 import Template
from urllib.parse import unquote, parse_qs
from requests_toolbelt.multipart import decoder

import threading, traceback, logging, signal, json, sys, ssl

functions = {}
templates_dir = "templates/"

logging_queue = Queue()
logger = logging.getLogger("Server")
server = socket(AF_INET, SOCK_STREAM)

def render_template(html, variables):
    template = Template(html)
    rendered = template.render(variables)

    return rendered

def _join(list_to_join, symbol_join_with):
    return symbol_join_with.join(list_to_join)

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
    splited_request = []
    is_POST = False
    is_GET = False
    link = ''
    headers = {}
    posted_json = {}

    while True:
        # reading
        message = b''
        
        data = conn.recv(4096)
        if not data:
            break

        message += data

        # split
        splited_request = message.split(b"\n")

        # get headers
        for i in splited_request:
            index = i.find(b": ")
            if index == -1:
                continue

            headers[i[:index]] = i[index+2:]
        # get method
        if splited_request[0].startswith(b"GET") and b"\r\n\r\n" in message:
            message = message.decode()
            is_GET = True
            break

        # post method   
        elif splited_request[0].startswith(b"POST") and b"\r\n\r\n" in message:
            # get content-lenght
            length_of_content = 0
            is_Content_length = False

            index = splited_request.index(b"\r") + 1
            read = b"\n".join(splited_request[index:])

            for i in splited_request:
                if i.startswith(b"Content-Length: "):
                    length_of_content = int(i[16:-1])
                    is_Content_length = True

            if not is_Content_length:
                while True:
                    tmp_data = conn.recv(1024)
                    if not tmp_data:
                        break
                    message += tmp_data.decode()
                    splited_request = message.split(b"\n")

                read = b"\n".join(splited_request[index:])

            else:
                # get body
                left_read = length_of_content - len(read)

                if left_read > 0:
                    count = 0
                    max_buffer_size = 16384

                    while True:
                        message += conn.recv(max_buffer_size)

                        count += 1

                        if left_read - count * max_buffer_size < 0:
                            break

                    splited_request = message.split(b"\n")
                    read = b"\n".join(splited_request[index:])

            # if bodies lenght doesnt equal excepted lenght we raise error
            print(len(read))
            if len(read) != length_of_content:
                html = read_file(templates_dir + "invalid_json_length.html")
                conn.sendall(b"HTTP/1.0 400 OK\r\n\r\n" + html.encode())

                conn.close()
                return

            is_POST = True
            break
    
    # get link
    if splited_request[0].startswith(b"GET"):
        link = splited_request[0][4:-10].decode()
    elif splited_request[0].startswith(b"POST"):
        link = splited_request[0][5:-10].decode()
    
    # get posted data
    if is_POST:
        for i in splited_request:
            i = i.decode().split(": ")
            if i[0] == "Content-Type" :
                # if content type equal json we parse json to dictionary
                if "application/json" in i[1]:
                    try:
                        index = splited_request.index(b"\r") + 1
                        posted_json = json.loads(b"\n".join(splited_request[index:]).decode())
                    except:
                        html = read_file(templates_dir + "json_format_error.html")
                        conn.sendall(b"HTTP/1.0 400 OK\r\n\r\n" + html.encode())
                        conn.close()
                        return

                    break

                # if content type equal form url we parse it to dictionary
                elif "application/x-www-form-urlencoded" in i[1]:
                    index = splited_request.index(b"\r") + 1
                    data = b"\n".join(splited_request[index:]).decode()
                    parsed_query = parse_qs(data)

                    posted_json = {key: value[0] for key, value in parsed_query.items()}

                    break
                
                # parse multi part
                elif "multipart/form-data" in i[1]:
                    index = splited_request.index(b"\r") + 1

                    multipart_string = b"\n".join(splited_request[index:])
                    decoded = decoder.MultipartDecoder(multipart_string, i[1])

                    field_name = decoded.parts

                    data = {}
                    for i in field_name:
                        result = {}

                        # data of file
                        if b"Content-Disposition" in i.headers:
                            files_data = i.headers[b"Content-Disposition"].decode().split("; ")
                            disposition = {"type": files_data[0]}
                            for j in files_data:
                                if "=" in j:
                                    index = j.index("=")
                                    disposition[j[:index]] = j[index + 1:]
                            
                            result["disposition"] = disposition

                        # content type
                        if b"Content-Type" in i.headers:
                            content_type = i.headers[b"Content-Type"].decode()
                            result["content-type"] = content_type

                        # is file
                        # if "attachment" in files_data:
                        #     pass
                            # print("its file")
                        # else:
                        #     pass
                            # print("its not file")

                        # content
                        content = i.content
                        result["content"] = content

                        # add to data
                        data[result["disposition"]["name"][1:-1]] = result

                    posted_json = data
                    break

                # if its another one we raise error cuz we cant parse it
                else:
                    html = read_file(templates_dir + "invalid_format_error.html")
                    conn.sendall(b"HTTP/1.0 400 OK\r\n\r\n" + html.encode())        
                    conn.close()
                    return
        
        getted_data = {}

        # if ? in link
        if link.find("?") != -1:
            # parse link
            link = unquote(link)
            a = link.index("?")

            data = link[a+1:]
            
            link = link[:a]

            # get data to dict
            parsed_query = parse_qs(data)
            getted_data = {key: value[0] for key, value in parsed_query.items()}

        try:
            if link in functions.keys():
                msg = functions[link](get_data=getted_data, post_data=posted_json)
                conn.sendall(b"HTTP/1.0 200 OK\r\n\r\n" + msg.encode())
            else:
                html = read_file(templates_dir + "404.html")
                conn.sendall(b"HTTP/1.0 404 OK\r\n\r\n" + html.encode())

        except Exception as err:
            error_exc = traceback.format_exc()
            logging_queue.put(["ERR", error_exc])
            conn.sendall(b"HTTP/1.0 500 Internal Server Error\r\n\r\nServer raised error: " + type(err).__name__.encode())

    # get "get"ted data
    elif is_GET and link.find("?") != -1:
        # parse link
        link = unquote(link)

        a = link.index("?")
        data = link[a+1:]

        link = link[:a]

        # get data to dict
        parsed_query = parse_qs(data)
        result = {key: value[0] for key, value in parsed_query.items()}

        try:
            if link in functions.keys():
                msg = functions[link](get_data=result)
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