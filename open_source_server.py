import logging
import os
import socket
import ssl
import struct
import time

import certifi
from dnslib import DNSRecord, server

logging.root.setLevel(os.getenv('LOGGING_LEVEL', logging.DEBUG))
CLOUDFLARE_DNS = '1.1.1.1'
context = ssl.create_default_context()
context.load_verify_locations(certifi.where())


class TlsDnsResolver(server.BaseResolver):
    def resolve(self, request, handler):
        logging.debug('got DNS request: \n%s', request)
        with socket.create_connection((CLOUDFLARE_DNS, 853)) as sock:
            with context.wrap_socket(sock, server_hostname=CLOUDFLARE_DNS) as ssock:
                data = request.pack()
                if len(data) > 65535:
                    raise ValueError(f'Packet too long: {len(data)}')
                data = struct.pack("!H", len(data)) + data
                ssock.sendall(data)
                response = ssock.recv(8192)
                length = struct.unpack("!H", bytes(response[:2]))[0]
                while len(response) - 2 < length:
                    response += ssock.recv(8192)
                response = response[2:]
                dns_response = DNSRecord.parse(response)
                logging.debug('got DNS response from cloudflare: \n%s', dns_response)
                return dns_response


if __name__ == '__main__':
    udp_server = server.DNSServer(resolver=TlsDnsResolver(), address='127.0.0.1', tcp=False)
    tcp_server = server.DNSServer(resolver=TlsDnsResolver(), address='127.0.0.1', tcp=True)

    try:
        logging.info('starting udp DNS server')
        udp_server.start_thread()
        logging.info('starting tcp DNS server')
        tcp_server.start_thread()
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.error('gracefully tearing down DNS server')
        pass
    except:
        logging.exception('Fatal error in DNS server execution')
        pass
    finally:
        udp_server.stop()
        tcp_server.stop()
