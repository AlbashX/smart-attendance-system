import base64
import http.client
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from scripts.mobile_server import make_handler


class Upstream(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(self.headers.get('Host', '').encode())
    def log_message(self, *args):
        pass


def test_mobile_auth_origin_and_proxy():
    backend = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
    gateway = ThreadingHTTPServer(('127.0.0.1', 0), make_handler('student', 'test-password', ['localhost'], backend.server_port))
    for server in (backend, gateway):
        threading.Thread(target=server.serve_forever, daemon=True).start()
    def request(headers):
        conn = http.client.HTTPConnection('127.0.0.1', gateway.server_port)
        conn.request('GET', '/api/state', headers={'Host': f'localhost:{gateway.server_port}', **headers})
        response = conn.getresponse()
        result = response.status, response.read()
        conn.close()
        return result
    token = 'Basic ' + base64.b64encode(b'student:test-password').decode()
    try:
        assert request({})[0] == 401
        assert request({'Authorization': 'Basic bad'})[0] == 401
        assert request({'Authorization': token, 'Origin': 'https://evil.example'})[0] == 403
        status, body = request({'Authorization': token, 'Origin': f'https://localhost:{gateway.server_port}'})
        assert status == 200
        assert body == f'127.0.0.1:{backend.server_port}'.encode()
        assert request({'Authorization': token, 'Host': 'evil.example'})[0] == 403
    finally:
        for server in (gateway, backend):
            server.shutdown()
            server.server_close()
