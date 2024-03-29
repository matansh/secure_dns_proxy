import logging
import socket
import ssl
import struct

import certifi
from dnslib import DNSRecord

CLOUDFLARE_DNS = '1.1.1.1'
context = ssl.create_default_context()
context.load_verify_locations(certifi.where())


def get_dns_request_over_udp(sock) -> (DNSRecord, str):
    data, client_address = sock.recvfrom(8192)
    return DNSRecord.parse(data), client_address


def get_dns_request_over_tcp(sock) -> DNSRecord:
    response = sock.recv(8192).strip()
    length = struct.unpack('!H', bytes(response[:2]))[0]
    while len(response) - 2 < length:
        new_data = sock.recv(8192).strip()
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
