from dnslib import DNSRecord


class DnsClient:
    def __init__(self, host, port, tcp=True):
        self.host = host
        self.port = port
        self.tcp = tcp

    def resolve_name(self, name: str) -> DNSRecord:
        res = DNSRecord.question(name).send(self.host, self.port, self.tcp)
        return DNSRecord.parse(res)
