import logging
import os
import socket
import struct
import time
from threading import Thread

from common import get_dns_request_over_tcp, cloudflare_dns_over_tls, get_dns_request_over_udp

ADDRESS = ('0.0.0.0', 53)
logging.root.setLevel(os.getenv('LOGGING_LEVEL', logging.DEBUG))


def udp_server():
    logging.info('starting UDP DNS server')
    with socket.socket(type=socket.SOCK_DGRAM) as sock:
        # making sure the socket is reusable as we expose tcp and udp on the same port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(ADDRESS)
        while True:
            try:
                dns_request, client_address = get_dns_request_over_udp(sock)
                dns_response = cloudflare_dns_over_tls(dns_request).pack()
                sock.sendto(dns_response, client_address)
            except:
                logging.exception('ERROR in udp server')
                continue


def tcp_server():
    logging.info('starting TCP DNS server')
    with socket.socket(type=socket.SOCK_STREAM) as sock:
        # making sure the socket is reusable as we expose tcp and udp on the same port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(ADDRESS)
        sock.listen(5)
        while True:
            try:
                conn, address = sock.accept()
                dns_request = get_dns_request_over_tcp(conn)
                dns_response = cloudflare_dns_over_tls(dns_request).pack()
                response = struct.pack('!H', len(dns_response)) + dns_response
                conn.sendall(response)
            except:
                logging.exception('ERROR in tcp server')
                continue


if __name__ == '__main__':
    thread_pool = [
        Thread(target=tcp_server),  # tcp
        Thread(target=udp_server)  # udp
    ]
    try:
        for thread in thread_pool:
            thread.start()
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.error('gracefully tearing down DNS servers')
        os._exit(0)
    except:
        logging.exception('Fatal error in DNS server execution')
        os._exit(1)
