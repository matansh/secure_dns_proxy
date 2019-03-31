import logging
import os
import socket
import struct
import time
from queue import Queue
from threading import Thread

from common import get_dns_request_over_tcp, cloudflare_dns_over_tls, get_dns_request_over_udp

ADDRESS = ('0.0.0.0', 53)
logging.root.setLevel(os.getenv('LOGGING_LEVEL', logging.DEBUG))


def udp_reader(sock, _queue: Queue):
    """ reads incoming dns queries from udp port, queues for future resolving """
    logging.info('starting UDP DNS reader')
    sock.bind(ADDRESS)
    while True:
        try:
            dns_request, client_address = get_dns_request_over_udp(sock)
            _queue.put((dns_request, client_address))
        except:
            logging.exception('ERROR reading from udp sock')
            continue


def udp_writer(sock, _queue: Queue):
    """ resolves queued dns queries, responds over udp port """
    logging.info('starting UDP DNS writer')
    while True:
        try:
            dns_request, client_address = _queue.get()
            dns_response = cloudflare_dns_over_tls(dns_request).pack()
            sock.sendto(dns_response, client_address)
            _queue.task_done()
        except:
            logging.exception('ERROR writing to udp sock')
            continue


def tcp_reader(sock, _queue: Queue):
    """ reads incoming dns queries from tcp port, queues for future resolving """
    logging.info('starting TCP DNS reader')
    sock.bind(ADDRESS)
    sock.listen(5)
    while True:
        try:
            connection, address = sock.accept()
            dns_request = get_dns_request_over_tcp(connection)
            _queue.put((dns_request, connection))
        except:
            logging.exception('ERROR reading from tcp sock')
            continue


def tcp_writer(_queue: Queue):
    """
    resolves queued dns queries, responds over udp port
    no sock parameter needed here as tcp response is over new sock object created at communication start
    """
    logging.info('starting TCP DNS writer')
    while True:
        try:
            dns_request, connection = _queue.get()
            dns_response = cloudflare_dns_over_tls(dns_request).pack()
            response = struct.pack('!H', len(dns_response)) + dns_response
            connection.sendall(response)
            _queue.task_done()
        except:
            logging.exception('ERROR writing to tcp sock')
            continue


if __name__ == '__main__':
    with socket.socket(type=socket.SOCK_DGRAM) as udp_sock:
        with socket.socket(type=socket.SOCK_STREAM) as tcp_sock:
            # making sure the socket is reusable as we expose tcp and udp on the same port
            udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            tcp_queue = Queue()
            udp_queue = Queue()

            thread_pool = [
                # tcp
                Thread(target=tcp_reader, args=(tcp_sock, tcp_queue)),
                Thread(target=tcp_writer, args=(tcp_queue,)),
                # udp
                Thread(target=udp_reader, args=(udp_sock, udp_queue)),
                Thread(target=udp_writer, args=(udp_sock, udp_queue))
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
