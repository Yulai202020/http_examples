import socket
import ssl

HOST = ("127.0.0.1", 8106)

# create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# create wrap socket
wraped_socket = ssl.create_default_context()
ssl_socket = wraped_socket.wrap_socket(s, server_hostname = HOST[0])

# connect to server with wrap socket
ssl_socket.connect(HOST)

# send message
ssl_socket.sendall(b"GET 127.0.0.1 HTTP/1.0\r\n\r\n")

# get message
message = ""

ssl_socket.shutdown(socket.SHUT_WR)

while True:
    data = ssl_socket.recv(1024)
    if not data:
        break
    message += data.decode()

print(message)

# close socket
ssl_socket.close()