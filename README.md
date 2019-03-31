Welcome to Matan Shalit's TLS DNS proxy implementation

## Server options:
#### `open_source_implementation.py`
If this task would be given to me as part of my development tasks I would not opt to implement everything from scratch.

Instead I would utilized open-sourced solutions in order to minimize development effort. 

This implementation represents how I would deliver this task without the requirement to develop my own solution from scratch.

#### `socketserver_implementation.py`
This implementation utilizes python's built-in high level `socketserver` api.

The `socketserver` library abstracts away a lot of "boilerplate" code needed to serve our interface. 

#### `socket_implmentation.py`
This implementation utilizes python's built-in low level `socket` api.

As this implementation does not use any abstraction layers like `socketserver` it implements all required steps in 
order to accept and return tcp/udp connections.

I implemented a very strait forward approach to serving the api's: in an endless loop -> read from socket.

For anything fancier then this "simple" implementation I would recommend using using higher level api's / open source utils.

## Execution
#### docker compose
Note: docker compose does not currently support exposing both tcp and udp for a single port.
As a result I had to create duplicates of every service (one for tcp and one for udp).  

Note2: docker compose does not support port discovery (`docker-compose port container "53/udp"` does not work). 
As a result I had to hard code the exposed container ports.

- $`docker-compose build`
- $`docker-compose up`
- in order to teardown created instances run $`docker-compose down`

#### python source
- install python 3.7 from www.python.org
- $`python3 -m venv venv`
- $`. venv/bin/activate`
- $`pip install -r requirements.txt`
- $`python -m <server_option>_implementation.py`

## Running the tests
- install python 3.7 from www.python.org
- $`python3 -m venv venv`
- $`. venv/bin/activate`
- $`pip install -r requirements.txt`
- $`pytest tests/`

## Production deployment in a micro-service architecture
- Depending on the scale of requests needed i would consider serving the dns-over-tls service behind some load balancing mechanism.
- All other services should be configured to utilize the dns-over-tls services ip (or the ip of the load-balancer) as their name resolver
- Given a kubernetes environment I would consider utilizing a k8s `service` to expose our dns-over-tls, 
k8s already has its own internal DNS service in order to resolve service and pod names so i would configure this k8s 
DNS service to "upstream" requests back to our dns-over-tls


## Security concerns
- DNS query is encrypted only on its second leg. communication from the origin of the request to our dns-over-tls service 
is still exposed and vulnerable to attack. 
- public certificate used to authenticate communication with cloudflare. 
  - creating a service to service auth schema, where our dns-over-tls service would have its own short lived encryption secrets would be better.
- Faulty DNS records? we could validate the resolved name from multiple providers to be sure that the DNS recoded was not tampered with at the source.
- The issue of trust, do we as an organisation trust cloudflare with our DNS queries? (cloudflare is an american company that may not conform to european privacy laws). 

## Possible improvements
- Single threaded async with python's `asyncio`
- Currently, for the sake of logging, we decode the incoming dns query and encode it back again before sending it to cloudflare
  - In a real production environment we would not waste this "meaningless" compute time

## Implementation notes
this code snippet:
```python
response = sock.recv(8192).strip()
length = struct.unpack('!H', bytes(response[:2]))[0]
while len(response) - 2 < length:
    new_data = sock.recv(8192)
    if not new_data:
        break
    response += new_data
response = response[2:]
```
featured in `common.get_dns_request_over_tcp` was derived from 
https://bitbucket.org/paulc/dnslib/src/9b80cd497f3d1b3b8260ee5fd9ae8eefa6b554d0/dnslib/server.py?at=default&fileviewer=file-view-default#server.py-126
