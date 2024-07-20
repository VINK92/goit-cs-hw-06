import http.server
import socketserver
import socket
import threading
import os
import urllib.parse
from datetime import datetime
from pymongo import MongoClient

# Конфігурація
HTTP_PORT = 3000
SOCKET_PORT = 5000
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
MONGO_URI = 'mongodb://mongo:27017'
DATABASE = 'message_db'
COLLECTION = 'messages'

# Налаштування клієнта MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE]
collection = db[COLLECTION]

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/message.html':
            self.path = '/message.html'
        elif self.path.startswith('/static/'):
            self.path = self.path.replace('/static', '')
        else:
            self.path = '/error.html'
            self.send_response(404)

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = urllib.parse.parse_qs(post_data.decode('utf-8'))
            username = data['username'][0]
            message = data['message'][0]

            # Відправка даних на Socket-сервер
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', SOCKET_PORT))
            sock.sendall(f'{username},{message}'.encode('utf-8'))
            sock.close()

            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

def start_http_server():
    os.chdir(STATIC_DIR)
    handler = SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", HTTP_PORT), handler) as httpd:
        print(f"HTTP сервер запущено на http://localhost:{HTTP_PORT}")
        httpd.serve_forever()

def start_socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', SOCKET_PORT))
    sock.listen(5)
    print(f"Socket сервер запущено на порту {SOCKET_PORT}")

    while True:
        client, addr = sock.accept()
        data = client.recv(1024).decode('utf-8')
        username, message = data.split(',')
        collection.insert_one({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "username": username,
            "message": message
        })
        client.close()

if __name__ == "__main__":
    threading.Thread(target=start_http_server).start()
    threading.Thread(target=start_socket_server).start()
