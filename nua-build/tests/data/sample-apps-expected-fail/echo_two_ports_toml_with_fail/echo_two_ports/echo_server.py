import multiprocessing as mp
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(f"<html>path: {self.path}</html>".encode("utf-8"))


def server(port: int):
    with HTTPServer(("", port), Handler) as http:
        http.serve_forever()


def echo_server(port: int):
    process = mp.Process(target=server, args=(port,))
    process.start()
