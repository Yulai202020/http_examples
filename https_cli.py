import hashlib, socket, ssl, sys, os
from requests_toolbelt import MultipartEncoder

# create binfile
filename = sys.argv[1]
count = sys.argv[2]
os.system(f"dd if=/dev/random of={filename} bs=1M count={count}")

HOST = ("192.168.100.37", 8220)

read = "framework/test.txt"
# create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# create wrap socket
wraped_socket = ssl.create_default_context()
ssl_socket = wraped_socket.wrap_socket(s, server_hostname = HOST[0])

# connect to server with wrap socket
ssl_socket.connect(HOST)

file_content = b""

with open(filename, "rb") as f:
    file_content = f.read()

sended_hash = hashlib.md5(file_content).hexdigest()

m = MultipartEncoder(fields = {"file": file_content})
multipart_string = m.to_string()

# send multipart/form-data
print(len(multipart_string))
ssl_socket.sendall(f"POST /hello HTTP/1.0\r\nContent-Length: {len(multipart_string)}\r\nContent-Type: {str(m.content_type)}\r\n\r\n".encode() + multipart_string)

message = b""

while True:
    data = ssl_socket.recv(1024)
    if not data:
        break
    message += data

print(message)


with open(read, "rb") as f:
    saved_hash = hashlib.md5(f.read()).hexdigest()

if saved_hash == sended_hash:
    print("Test passed")
else:
    print("Test failed")


# close socket
ssl_socket.close()