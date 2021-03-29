## TCP Server

The TCP server component.

### TCP Server object

The object is defined in [defines.py](./TCPServer/defines.py).
The server can handle several client sessions.
The IP, port and other parameters are defined in [default.cfg](./Settings/default.cfg)
The message protocol and workload programs are under development.

### Interface

We provides console interface to manage the server.
It writes in [server.py](./TCPServer/server.py).

### Usage

The server starts in simple code:

```python
from TCPServer import server

server.interface()
```

If you want to use the server directly,
here is the core code to start the server.

```python
from .defines import TCPServer

server = TCPServer()
server.start()
```
