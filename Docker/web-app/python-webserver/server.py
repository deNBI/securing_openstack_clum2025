from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

class S(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Welcome to CLUM 2025 Secure a Webservice')

if __name__ == "__main__":
    PORT = 8080
    Handler = S
    httpd = socketserver.TCPServer(("", PORT), Handler)
    print("serving at port", PORT)
    httpd.serve_forever()
