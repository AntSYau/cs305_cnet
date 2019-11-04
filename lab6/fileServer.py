import asyncio
from pathlib import Path
from urllib.parse import unquote
from datetime import timedelta, datetime

extensions = {
    ".jpg": b'image/jpeg',
    ".txt": b'text/plain',
    ".xml": b'text/xml',
    ".png": b'image/png',
    ".json": b'application/json',
    ".pdf": b'application/pdf',
    ".docx": b'application/msword'
}  # i could include more extensions in this dictionary, but that contributes little and I really need time to finish
# my OOAD project (again).

mna405 = [
    b'HTTP/1.0 405 Method Not Allowed\r\n',
    b'Content-Type:text/html; charset=utf-8\r\n',
    b'Connection: close\r\n',
    b'\r\n',
    b'<html><body><h1>405 Method Not Allowed</h1><body></html>\r\n',
    b'\r\n'
]

nf404 = [
    b'HTTP/1.0 404 Not Found\r\n',
    b'Content-Type:text/html; charset=utf-8\r\n',
    b'Connection: close\r\n',
    b'\r\n',
    b'<html><body><h1>404 Not Found</h1><body></html>\r\n',
    b'\r\n'
]


def generate_index(path: Path) -> list:
    ret = []
    dirs = [x for x in path.iterdir() if x.is_dir()]
    dirs.sort()
    for d in dirs:
        ret.append(b'<a href="' + d.name.encode() + b'/">' + d.name.encode() + b'/</a></br>')
    files = [x for x in path.iterdir() if x.is_file()]
    files.sort()
    for f in files:
        ret.append(b'<a href="' + f.name.encode() + b'">' + f.name.encode() + b'</a></br>')
    return ret


async def dispatch(reader, writer):
    data = {}
    fields = []
    while True:
        append = await reader.readline()  # wait for request
        if append == b'\r\n' or data == b'':
            break
        append = bytes.decode(append)
        if ":" not in append:
            fields = append.split(' ')
            continue
        append = str.splitlines(append)[0].split(": ")
        data[append[0]] = append[1]
    print(fields)
    if fields[0] not in ['GET', 'HEAD']:  # return 405 for bad requires
        writer.writelines(mna405)
        await writer.drain()
        writer.close()
        return
    dest = Path("." + unquote(fields[1]))
    if not dest.exists():  # return 404 for non-existing dir
        writer.writelines(nf404)
        await writer.drain()
        writer.close()
        return
    cookie_jar = {}
    if "Cookie" in data.keys():
        cookie_fields = data["Cookie"].split('; ')
        for i in cookie_fields:
            cookie_record = i.split('=')
            cookie_jar[cookie_record[0]] = cookie_record[1]
    print([dest])
    print("Cookie Jar:", cookie_jar)
    print(dest == Path('.') or dest == Path('./'))
    print('lastdir' in cookie_jar.keys())
    if dest.is_file() and fields[0] == 'GET':  # if request is a file
        ctype = b'application/octet-stream'
        if dest.suffix in extensions:
            ctype = extensions[dest.suffix]
        if "Range" not in data.keys():
            header = [
                b'HTTP/1.0 200 OK\r\n',
                b'Content-Type: ' + ctype + b'\r\n',
                b'Content-Length: ' + str(dest.stat().st_size).encode() + b'\r\n',
                b'Connection: close\r\n',
                b'\r\n'
            ]

            file = open(str(dest), 'rb')  # open dest in rb mode
        else:
            header = [
                b'HTTP/1.0 200 OK\r\n',
                b'Content-Type: ' + ctype + b'\r\n',
                b'Content-Length: ' + str(dest.stat().st_size).encode() + b'\r\n',
                b'Connection: close\r\n',
                b'\r\n'
            ]
        writer.writelines(header)
        writer.write(file.read())  # write to response
        writer.write(b'\r\n')
    elif (dest == Path('.') or dest == Path('./')) \
            and 'lastdir' in cookie_jar.keys() \
            and 'Referer' not in data.keys():
        writer.writelines([
            b'HTTP/1.0 302 Found\r\n',
            b'Content-Type:text/html; charset=utf-8\r\n',
            b'Connection: close\r\n',
            b'Location: ' + cookie_jar["lastdir"].encode() + b'\r\n',
            b'\r\n'])
    else:  # if dest is a directory
        setcookie = b''
        if not (dest == Path('.') or dest == Path('./')):
            setcookie = b'Set-Cookie: lastdir=' + fields[1].encode() + b'; path=/; expires=' \
                        + datetime.strftime(datetime.utcnow() + timedelta(days=2),
                                            "%a, %d-%b-%Y %H:%M:%S GMT").encode() + b'\r\n'
        else:
            setcookie = b'Set-Cookie: lastdir=; path=/; expires=' \
                        + datetime.strftime(datetime.utcnow() - timedelta(days=2),
                                            "%a, %d-%b-%Y %H:%M:%S GMT").encode() + b'\r\n'
        to_write = [
            b'HTTP/1.0 200 OK\r\n',
            b'Content-Type:text/html; charset=utf-8\r\n',
            b'Connection: close\r\n',
            setcookie,
            b'\r\n',
            b'<html><head>\r\n']
        # print(to_write)
        writer.writelines(to_write)
        if fields[1][
            -1] != '/':  # bug found: if user is at /A/B (without the last '/') and href is to C/, then HTML will
            # redirect user to /A/C/ instead of /A/B/C/, which causes 404 error.
            # so if user is at /A/B, we must force redirect user to /A/B/ (with the last '/').
            # The last '/' really matters!!!!!!!!!!
            writer.writelines([b'<meta http-equiv="Refresh" content="0;url=' + fields[1].encode() + b'/">'])
        writer.writelines([
            b'</head><body>\r\n',
            b'<h1>Index of ' + bytes(dest) + b'</h1><hr><pre>\r\n'
        ])
        if fields[1] != '/':  # if current dir is not root dir, then add a link to allow users to go to the upper level.
            writer.writelines([b'<a href="../">..(upper level)</a></br>'])
        writer.writelines(generate_index(dest))  # generate_index() generates index and returns a list of HTML links.
        writer.writelines([  # end of HTML
            b'</pre></hr></body></html>\r\n',
            b'\r\n'
        ])
    await writer.drain()  # break operation
    writer.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    listener = asyncio.start_server(dispatch, host='0.0.0.0', port=8080, loop=loop)  # listen on 8080
    server = loop.run_until_complete(listener)
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()  # start server
    except Exception as e:
        print(str(e))
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
