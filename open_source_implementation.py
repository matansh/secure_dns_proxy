import logging
import os
import time

from dnslib import server

from common import cloudflare_dns_over_tls

logging.root.setLevel(os.getenv('LOGGING_LEVEL', logging.DEBUG))


class TlsDnsResolver(server.BaseResolver):
    def resolve(self, request, handler):
        return cloudflare_dns_over_tls(request)


if __name__ == '__main__':
    serve_address = '0.0.0.0'
    udp_server = server.DNSServer(resolver=TlsDnsResolver(), address=serve_address, tcp=False)
    tcp_server = server.DNSServer(resolver=TlsDnsResolver(), address=serve_address, tcp=True)

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
    except Exception:
        logging.exception('Fatal error in DNS server execution')
        pass
    finally:
        udp_server.stop()
        tcp_server.stop()
