import pytest

from tests.dns_client import DnsClient


@pytest.mark.parametrize('port, is_tcp', [
    (4001, True),
    (4002, False),
    (4003, True),
    (4004, False),
    (4005, True),
    (4006, False)
])
class TestDnsSolutions:
    @pytest.mark.parametrize('name', ['bad.url.com.nonexsisting', '127.0.0.1'])
    def test_invalid_dns_name(self, port: int, is_tcp: bool, name: str):
        response = DnsClient('127.0.0.1', port, is_tcp).resolve_name(name)
        assert name in str(response.questions[0])
        assert str(response.rr) == '[]'

    @pytest.mark.parametrize('name', ['facebook.com', 'google.com', 'w3c.org'])
    def test_valid_dns_name(self, port: int, is_tcp: bool, name: str):
        response = DnsClient('127.0.0.1', port, is_tcp).resolve_name(name)
        assert name in str(response.questions[0])
        assert name in str(response.rr)
