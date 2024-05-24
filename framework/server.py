from my_framework_v2 import *

def index():
    html = ""
    with open("index.html") as f:
        html = f.read()
    return html

def hello(result):
    return "hi " + result["name"] + " " + result["surname"]

def hello_yulai():
    return "hi yulai"

bind(index, "/")
bind(hello, "/hello")
bind(hello_yulai, "/hello_yulai")

start_server(host="0.0.0.0", port=8135, protocol="https", is_logging=True, logsfile_path="logs.log")