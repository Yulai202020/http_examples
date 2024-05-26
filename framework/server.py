from my_framework_v2 import *

# example index
def index():
    html = ""
    with open("index.html") as f:
        html = f.read()

    return render_template(html, {"name": "yulai"})

# post example
# here can be /hello?name=yulai
# and can be post request
def hello(get_data, post_data):
    with open("hello.html") as f:
        html = f.read()
    
    print(get_data)
    print(post_data)

    return render_template(html, {"a": list(get_data.keys()), "b": list(get_data.values()), "len": len(get_data)})

# example get
def hello_yulai(get_data):
    return "hi yulai"

bind(index, "/")
bind(hello, "/hello")
bind(hello_yulai, "/hello_yulai")

start_server(host="0.0.0.0", port=8154, protocol="https", is_logging=True, logsfile_path="logs.log")