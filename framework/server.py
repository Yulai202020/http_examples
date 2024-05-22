from my_framework_v2 import *

def index():
    html = ""
    with open("index.html") as f:
        html = f.read()
    return html

def hello(result):
    print(result)
    return "hi " + result["name"]

bind(index, "/")
bind(hello, "/hello")

start_server("127.0.0.1", 8106)