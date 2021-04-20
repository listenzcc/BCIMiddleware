import time
import struct
import socket
import threading
import numpy as np
from .BCIDecoder import generate_simulation_data

from . import logger

simulationMode = True
maxLength = 3600  # Seconds


class SimulationDataGenerator(object):
    ''' Generate simulation data '''

    def __init__(self):
        ''' Initialize the simulation data '''
        self.all_data, _ = generate_simulation_data()
        self.raw = self.all_data.copy()
        self.ptr = 0
        logger.debug(f'Simulation data ({self.all_data.shape}) is generated.')

    def reset(self):
        ''' Reset the simulation data generator,
        the generator will work as it was initialized.
        '''
        self.all_data = self.raw
        self.ptr = 0
        logger.debug(
            f'Simulation restarted from begining, the data has been restored.')

    def pop(self, length=40):
        ''' Pop the simulation data from the top [length]

        Args:
        - @length: The length to be popped from the top.
        '''
        if length < self.all_data.shape[1]:
            d = self.all_data[:, :length]
            self.all_data = self.all_data[:, length:]
            # logger.debug(f'Normally fetch data for {length}.')
            return d

        if length == self.all_data.shape[1]:
            d = self.all_data.copy()
            # logger.debug(f'Normally fetch data for {length}.')
            self.all_data = self.raw
            logger.debug(f'Current data is empty, restart from begining.')
            return d

        if length < self.all_data.shape[1]:
            d0 = self.all_data.copy()
            logger.debug(f'Partly fetch data 1 for {d0.shape[1]}.')
            self.all_data = self.raw
            logger.debug(f'Current data is empty, restart from begining.')
            length -= d0.shape[1]
            d1 = self.all_data[:, :length]
            logger.debug(f'Partly fetch data 2 for {length}.')
            self.all_data = self.all_data[:, length:]
            return np.concatenate([d0, d1], axis=1)

        logger.error(f'Can not fetch data as request, length is "{length}"')
        return None


class NeuroScanDeviceClient(object):
    '''NeuroScan Device Client.

    The communication is in TCP socket,
    the process is:
    1.1. Connect to the device, @connect;
    1.2. Send start scan request to device;
    2. Start acquisition, @start_acq;
    3. The device will send data every 0.04 seconds;
    4. Stop acquisition, @stop_acq;
    5.1. Send stop scan request to device;
    5.2. Disconnect from the device, @disconnect.
    '''

    def __init__(self, ip_address, port, sample_rate, n_channels, time_per_packet=0.04, simulationMode=simulationMode, maxLength=maxLength):
        '''Initialize with Basic Parameters,
        and connect to the device.

        Args:
        - @ip_address: The IP address of the device;
        - @port: The port of the device;
        - @sample_rate: The sample rate;
        - @n_channels: The number of channels;
        - @time_per_packet: The time gap between two packet from the device, the default value is 0.04 seconds;
        - @simulationMode: If use simulation mode, in simulation mode, the EEG Device is ignored, the data will be automatically generated;
        - @maxLength: The max length of the data, the unit is in seconds.
        '''
        self.simulationMode = simulationMode

        self.maxLength = maxLength

        self.ip_address = ip_address
        self.port = port
        self.sample_rate = sample_rate
        self.n_channels = n_channels
        self.time_per_packet = time_per_packet
        self.compute_bytes_per_package()

        self._clear()

        logger.info(f'EEG Device client initialized.')

        if not simulationMode:
            self.connect()
        else:
            self.sdg = SimulationDataGenerator()
            logger.info(f'Simulation mode is used')

    def _clear(self):
        ''' Clear data '''
        self.data = np.zeros((self.n_channels, maxLength * self.sample_rate))
        self.data_length = 0
        logger.info(
            f'Created new data pool as zero matrix of {self.data.shape}')

    def _add(self, d):
        ''' Accumulate new data chunk [d] into data '''
        n = d.shape[1]

        if not self.data_length + n < self.data.shape[1]:
            logger.error(
                f'The time limit of the data is reached. New data is ignored.')
            return

        self.data[:, self.data_length:self.data_length+n] = d
        self.data_length += n

    def compute_bytes_per_package(self):
        '''Compute the length of bytes in every data packet

        Generates:
        - @packet_time_point: The time points in each packets;
        - @bytes_per_packet: The bytes length in each packet.
        '''
        packet_time_point = int(
            np.round(self.sample_rate * self.time_per_packet))
        bytes_per_packet = (self.n_channels + 1) * packet_time_point * 4
        self.packet_time_point = packet_time_point
        self.bytes_per_packet = bytes_per_packet

    def _unpack_data_fmt(self):
        '''Generate built-in format for unpacking the data

        Outs:
        - The format.
        '''
        return '<' + str((self.n_channels + 1) * self.packet_time_point) + 'i'

    def _unpack_header(self, header_packet):
        '''The method of unpacking header.

        Args:
        - @header_packet: The header packet to be unpacked.

        Outs:
        - The contents in the header.
        '''
        chan_name = struct.unpack('>4s', header_packet[:4])
        w_code = struct.unpack('>H', header_packet[4:6])
        w_request = struct.unpack('>H', header_packet[6:8])
        packet_size = struct.unpack('>I', header_packet[8:])
        return (chan_name[0], w_code[0], w_request[0], packet_size[0])

    def _unpack_data(self, data_packet):
        '''The method of unpacking data.

        Args:
        - @data_packet: The data packet to be unpacked.

        Outs:
        - The data in matrix, the shape is (n_channels x time_points).
        '''
        data_trans = np.asarray(struct.unpack(self._unpack_data_fmt(),
                                              data_packet)).reshape((-1, self.n_channels + 1)).T
        return data_trans

    def connect(self):
        '''Connect to the device,
        and start acquisition.
        '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SEND_BUF_SIZE = self.bytes_per_packet
        RECV_BUF_SIZE = self.bytes_per_packet * 9

        self.client.connect((self.ip_address, self.port))
        self.client.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.client.setsockopt(
            socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUF_SIZE)
        self.client.setsockopt(
            socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_BUF_SIZE)
        logger.info('Established the connection to EEG Device.')

        # Send start acquisition request
        self.send(struct.pack('12B', 67, 84, 82, 76, 0, 2, 0, 1, 0, 0, 0, 0))

        # Receive reply
        header_packet = self.receive_data(24)
        logger.debug(f'Received reply for ACQ request: {header_packet}')

    def send(self, msg):
        '''Send message to the device.

        Args:
        - @msg: The message to be sent, it should be of bytes.
        '''
        self.client.send(msg)
        logger.debug(f'Sent {msg}')

    def start_send(self):
        '''Send start sending message to the device.
        A thread will be started to collecting data from the device.

        Vars:
        - @data: Where the data will be stored in;
        - @data_length: The accumulated length of the data;
        - @collecting: The flag of collecting.
        '''
        self._clear()
        self.collecting = True

        if self.simulationMode:
            self.sdg.reset()
            logger.debug(
                f'Not sending start sending message in simulation mode')
        else:
            self.send(struct.pack('12B', 67, 84, 82,
                                  76, 0, 3, 0, 3, 0, 0, 0, 0))

        t = threading.Thread(target=self.collect)
        t.setDaemon(True)
        t.start()

    def collect(self):
        '''The collecting method used by start_acq.
        - It will collect data until [collecting] is set to False;
        - It will report data length every 1000 units;
        - It may complain about connection aborted on close, it is fine.
        '''
        logger.info('Collection Start.')
        while self.collecting:
            try:
                d = self.get_data()
                self._add(d)
                if self.data_length % self.sample_rate == 0:
                    logger.debug(
                        f'Accumulated data length: {self.data_length}')
            except ConnectionAbortedError:
                logger.warning(
                    'Connection to the device is closed. This can be normal if collecting is done.')
                break
        logger.info('Collection Done.')

    def get_data(self):
        '''Get the data form the latest packet.
        The packet is in two parts:
        - header: The latest separation shows the length of the data body;
        - data: The data body;
        - The length of the data body should be equal with the [bytes_per_packet] as prior computed.

        Outs:
        - new_data_temp: The latest data, the shape is (n_channels x time_points(0.04 seconds)).
        '''
        if self.simulationMode:
            time.sleep(self.time_per_packet)
            return self.sdg.pop(self.packet_time_point)
            # return np.ones((self.n_channels, self.packet_time_point))
        else:
            tmp_header = self.receive_data(12)
            details_header = self._unpack_header(tmp_header)

            if details_header[-1] == self.bytes_per_packet:
                pass
            else:
                print(
                    f'Warning, received data has {details_header[-1]} bytes, and required data should have {self.bytes_per_packet} bytes. The EEG channels setting may be incorrect')

            bytes_data = self.receive_data(self.bytes_per_packet)
            new_data_trans = self._unpack_data(bytes_data)

            new_data_temp = np.empty(new_data_trans.shape, dtype=np.float)
            new_data_temp[:-1, :] = new_data_trans[:-1, :] * 0.0298  # 单位 uV
            new_data_temp[-1, :] = np.zeros(new_data_trans.shape[1])

            return new_data_temp

    def get_all(self):
        '''Get the accumulated data as a matrix, the shape is (n_channels x time_points(accumulated)).

        Outs:
        - The accumulated data.
        '''
        return self.data[:, :self.data_length]

    def receive_data(self, n_bytes):
        '''The built-in method of receiving [n_bytes] length bytes from the device,
        it will read the buffer until it reached to the [n_bytes] length.

        Args:
        - @n_bytes: The length of the bytes to be fetched.

        Outs:
        - The [n_bytes] length bytes.
        '''
        b_data = b''
        flag_stop_recv = False
        b_count = 0

        while not flag_stop_recv:
            tmp_bytes = self.client.recv(n_bytes - b_count)

            if b_count == n_bytes or not tmp_bytes:
                flag_stop_recv = True

            b_count += len(tmp_bytes)
            b_data += tmp_bytes

        return b_data

    def stop_send(self):
        '''Send stopping sending message to the device,
        and the collecting threading will be stopped accordingly,
        it will also clear the existing contents in the buffer.
        '''
        self.collecting = False
        time.sleep(0.1)
        if self.simulationMode:
            logger.debug(f'Not send stop sending message in simulation mode')
        else:
            self.send(struct.pack('12B', 67, 84, 82,
                                  76, 0, 3, 0, 4, 0, 0, 0, 0))
        self.get_data()

    def disconnect(self):
        '''Disconnect from the device.
        '''
        if self.simulationMode:
            logger.debug(
                f'Not send closing connection message in simulation mode')
        else:
            # Send stop acquisition request
            self.send(struct.pack('12B', 67, 84, 82,
                                  76, 0, 2, 0, 2, 0, 0, 0, 0))
            # Send close connection request
            self.send(struct.pack('12B', 67, 84, 82,
                                  76, 0, 1, 0, 2, 0, 0, 0, 0))
            self.client.close()
        logger.info(f'Closed Connection to Device.')
