import socket

HOST = ("127.0.0.1", 8080)

# create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(HOST)

# send message
s.sendall(b"GET 127.0.0.1 HTTP/1.0\r\n\r\n")
# get message
message = ""

s.shutdown(socket.SHUT_WR)

while True:
    data = s.recv(1024)
    if not data:
        break
    message += data.decode()

print(message)

# close socket
s.close()