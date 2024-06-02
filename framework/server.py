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

    with open("test.txt", "wb") as f:
        f.write(post_data["file"]["content"])
    
    # return render_template(html, {"a": list(post_data.keys()), "b": list(post_data.values()), "len": len(post_data)})
    return html

# example get
def login():
    with open("login.html") as f:
        html = f.read()
    return html

def idk(get_data):
    with open("hello.html") as f:
        html = f.read()
    return render_template(html, {"a": list(get_data.keys()), "b": list(get_data.values()), "len": len(get_data)})

bind(index, "/")
bind(hello, "/hello")
bind(login, "/login")
bind(idk, "/idk")

start_server(host="0.0.0.0", port=8220, protocol="https", is_logging=True, logsfile_path="logs.log")