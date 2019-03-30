import logging
import os
import struct
import time
from socketserver import TCPServer, UDPServer, BaseRequestHandler
from threading import Thread

from dnslib import DNSRecord

from common import get_dns_request_over_tcp, cloudflare_dns_over_tls

logging.root.setLevel(os.getenv('LOGGING_LEVEL', logging.DEBUG))


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
    serving_address = ('0.0.0.0', 53)
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
