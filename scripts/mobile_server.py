"""Password-protected LAN HTTPS gateway to the unchanged loopback application."""
import argparse
import base64
import hmac
import http.client
import ipaddress
import json
from pathlib import Path
import secrets
import ssl
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local/mobile'


def make_handler(username, password, hosts, backend_port=8000):
    expected = 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()
    class Gateway(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def handle_request(self):
            host = self.headers.get('Host', '')
            if urlsplit('https://' + host).hostname not in hosts:
                self.send_error(403)
                return
            if not hmac.compare_digest(self.headers.get('Authorization', '').encode(), expected.encode()):
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm="Attend local prototype"')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                return
            origin = self.headers.get('Origin')
            if origin and origin != 'https://' + host:
                self.send_error(403)
                return
            if self.headers.get('Transfer-Encoding') or not self.path.startswith('/') or self.path.startswith('//'):
                self.send_error(400)
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self.send_error(400)
                return
            if not 0 <= length <= 10_000_000:
                self.send_error(413)
                return
            self.connection.settimeout(60)
            data = self.rfile.read(length) if length else None
            headers = {k:v for k,v in self.headers.items() if k.lower() not in {'host','origin','authorization','connection','transfer-encoding','forwarded','x-forwarded-host','x-forwarded-proto'}}
            headers['Host'] = f'127.0.0.1:{backend_port}'
            if origin:
                headers['Origin'] = f'http://127.0.0.1:{backend_port}'
            conn = http.client.HTTPConnection('127.0.0.1', backend_port, timeout=60)
            try:
                conn.request(self.command, self.path, body=data, headers=headers)
                response = conn.getresponse()
                body = response.read()
                self.send_response(response.status)
                for key,value in response.getheaders():
                    if key.lower() not in {'connection','transfer-encoding','server','date','content-length'}:
                        self.send_header(key,value)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                if self.command != 'HEAD':
                    self.wfile.write(body)
            except (OSError, http.client.HTTPException):
                self.send_error(502, 'Start the local application using start.ps1')
            finally:
                conn.close()
        do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = handle_request
    return Gateway


def initialize(address):
    from datetime import datetime, timedelta, timezone
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
    ipaddress.ip_address(address)
    LOCAL.mkdir(parents=True, exist_ok=True)
    config_path = LOCAL/'config.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {'username':'student','password':secrets.token_urlsafe(24)}
    config['address'] = address
    key_path = LOCAL/'ca.key'
    now = datetime.now(timezone.utc)
    if key_path.exists():
        key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
        ca = x509.load_pem_x509_certificate((LOCAL/'ca.pem').read_bytes())
    else:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Attend Laptop Local CA')])
        ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
              .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5))
              .not_valid_after(now+timedelta(days=365)).add_extension(x509.BasicConstraints(ca=True,path_length=0),True)
              .add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),True).sign(key,hashes.SHA256()))
        key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        (LOCAL/'ca.pem').write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    (LOCAL/'attend-root.cer').write_bytes(ca.public_bytes(serialization.Encoding.DER))
    server_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    cert = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,address)]))
            .issuer_name(ca.subject).public_key(server_key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=90))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(address)),x509.IPAddress(ipaddress.ip_address('127.0.0.1')),x509.DNSName('localhost')]),False)
            .add_extension(x509.BasicConstraints(ca=False,path_length=None),True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),False).sign(key,hashes.SHA256()))
    (LOCAL/'server.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    (LOCAL/'server.key').write_bytes(server_key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    config_path.write_text(json.dumps(config,indent=2))
    (LOCAL/'PHONE-SETUP.txt').write_text(f'Open https://{address}:8443 after installing attend-root.cer as a trusted local CA on your phone.\nUsername: {config["username"]}\nPassword: {config["password"]}\nKeep this file and all .key files private. Share only attend-root.cer with your own test phones.\n')
    print(f'HTTPS configured for https://{address}:8443. Credentials are in .local/mobile/PHONE-SETUP.txt')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', metavar='LAN_IP')
    args = parser.parse_args()
    if args.init:
        initialize(args.init)
        return
    config = json.loads((LOCAL/'config.json').read_text())
    server = ThreadingHTTPServer((config['address'],8443),make_handler(config['username'],config['password'],[config['address'],'localhost','127.0.0.1']))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(LOCAL/'server.pem', LOCAL/'server.key')
    server.socket = context.wrap_socket(server.socket,server_side=True)
    print(f'Attend mobile gateway: https://{config["address"]}:8443',flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
