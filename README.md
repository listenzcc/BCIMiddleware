# BCIMiddleware

The middleware of BCI computing, BCI communicating, and other necessary stuff.

# Components

## Logger

Generate logger by one sentence:

```python
from logger import logger
```

**Notions**:

1. My EasyLogging package is used to generate the 'logger',
   be sure it is in your python environment.

2. The logging file will be in the 'logs' folder beside the package,
   make sure the folder exists.

3. The logger will be automatically named as the created time.
   To prevent the logging being recorded into separate files,
   I suggest the users to generate the 'logger' and use it across the whole connected functions or packages.

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

## Work Load Simulation

The folder is the simulation to TCP clients in real work load.

### Usage

The users can start several clients for simulation.

```sh
# Make sure you are in the folder of "WorkLoadSimulation"
cd WorkLoadSimulation

# It will start three terminals to simulate three clients
python new_client.py
```


# Development Diary

## 2020-03-29

1. Start the project;
2. Add logging component to the project;
3. Add readme.py to summary the .md file in components.

## 2020-03-31

1. Develop TCP communication components;
2. Finish basic communication function of TCP server development;
3. Finish workload simulation for TCP clients.
