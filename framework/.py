
content_type = "multipart/form-data; boundary=ce560532019a77d83195f9e9873e16a1"
decoded = decoder.MultipartDecoder(multipart_string, content_type)

field_name = decoded.parts

data = {}

for i in field_name:
    # data of file
    files_data = i.headers["Content-Disposition"].decode().split("; ")

    # content type
    try:
        content_type = i.headers["Content-Type"].decode()
    except:
        pass

    # content
    content = i.content.decode()