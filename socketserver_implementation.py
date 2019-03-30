import logging
import os
import socket
import ssl
import struct
import time
from socketserver import TCPServer, UDPServer, BaseRequestHandler
from threading import Thread

import certifi
from dnslib import DNSRecord

logging.root.setLevel(os.getenv('LOGGING_LEVEL', logging.DEBUG))
CLOUDFLARE_DNS = '1.1.1.1'
context = ssl.create_default_context()
context.load_verify_locations(certifi.where())


def get_dns_request_over_tcp(sock) -> DNSRecord:
    response = sock.recv(8192).strip()
    length = struct.unpack('!H', bytes(response[:2]))[0]
    while len(response) - 2 < length:
        new_data = sock.recv(8192)
        if not new_data:
            break
        response += new_data
    response = response[2:]
    return DNSRecord.parse(response)


def cloudflare_dns_over_tls(dns_request: DNSRecord) -> DNSRecord:
    logging.debug('handling DNS request: \n%s', dns_request)
    with socket.create_connection((CLOUDFLARE_DNS, 853)) as sock:
        with context.wrap_socket(sock, server_hostname=CLOUDFLARE_DNS) as ssock:
            data = dns_request.pack()
            if len(data) > 65535:
                raise ValueError(f'Packet too long: {len(data)}')
            data = struct.pack('!H', len(data)) + data
            ssock.sendall(data)
            dns_response = get_dns_request_over_tcp(ssock)
            logging.debug('got DNS response from cloudflare: \n%s', dns_response)
            return dns_response


class ReusableTCPServer(TCPServer):
    allow_reuse_address = True


class ReusableUDPServer(UDPServer):
    allow_reuse_address = True


class DnsTcpHandler(BaseRequestHandler):
    def handle(self):
        dns_request = get_dns_request_over_tcp(self.request)
        dns_response = cloudflare_dns_over_tls(dns_request).pack()
        response = struct.pack('!H', len(dns_response)) + dns_response
        self.request.sendall(response)


class DnsUdpHandler(BaseRequestHandler):
    def handle(self):
        data, connection = self.request
        response = cloudflare_dns_over_tls(DNSRecord.parse(data)).pack()
        connection.sendto(response, self.client_address)


if __name__ == '__main__':
    logging.info('starting DNS server')
    serving_address = ('127.0.0.1', 53)
    tcp_server = ReusableTCPServer(serving_address, DnsTcpHandler)
    udp_server = ReusableUDPServer(serving_address, DnsUdpHandler)

    thread_pool = [
        Thread(target=tcp_server.serve_forever),
        Thread(target=udp_server.serve_forever)
    ]
    try:
        for thread in thread_pool:
            thread.start()
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.error('gracefully tearing down DNS server')
        os._exit(0)
    except:
        logging.exception('Fatal error in DNS server execution')
        os._exit(1)
