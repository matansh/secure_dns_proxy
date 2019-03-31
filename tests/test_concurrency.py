import logging
import time
from threading import Thread, Event

from tests.dns_client import DnsClient


def run_dns_queries(port, is_tcp, did_fail_event: Event):
    for name in ['imdb.com', 'google.com', 'ynet.co.il', 'cnn.com', 'paypal.com',
                 'w3schools.com', 'python.org', 'eventer.co.il', 'mako.co.il', 'stackoverflow.com']:
        try:
            DnsClient('127.0.0.1', port, is_tcp).resolve_name(name)
        except:
            logging.exception('failed to resolve name: %s, over protocol: %s', name, 'tcp' if is_tcp else 'udp')
            did_fail_event.set()
            exit(1)
    exit(0)


def test_concurrency():
    did_fail = Event()
    did_fail.clear()
    thread_pool = [
        Thread(target=run_dns_queries, args=(4007, True, did_fail)),
        Thread(target=run_dns_queries, args=(4007, True, did_fail)),
        Thread(target=run_dns_queries, args=(4008, False, did_fail)),
        Thread(target=run_dns_queries, args=(4008, False, did_fail))
    ]
    time.sleep(3)
    for thread in thread_pool:
        thread.start()

    for thread in thread_pool:
        thread.join()

    assert not did_fail.is_set()
