import time
import struct
import socket
import threading
import numpy as np

from . import logger


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

    def __init__(self, ip_address, port, sample_rate, n_channels):
        '''Initialize with Basic Parameters,
        and connect to the device.

        Args:
        - @ip_address: The IP address of the device;
        - @port: The port of the device;
        - @sample_rate: The sample rate;
        - @n_channels: The number of channels.
        '''
        self.ip_address = ip_address
        self.port = port
        self.sample_rate = sample_rate
        self.n_channels = n_channels
        self.compute_bytes_per_package()
        logger.info(f'EEG Device client initialized.')
        self.connect()

    def compute_bytes_per_package(self, time_per_packet=0.04):
        '''Compute the length of bytes in every data packet

        Args:
        - @time_per_packet: The interval between two data packets from the device.

        Generates:
        - @packet_time_point: The time points in each packets;
        - @bytes_per_packet: The bytes length in each packet.
        '''
        packet_time_point = int(np.round(self.sample_rate * time_per_packet))
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
        and start scanning.
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

        self.send(struct.pack('12B', 67, 84, 82, 76,
                              0, 2, 0, 1, 0, 0, 0, 0))  # 开始获取数据

        header_packet = self.receive_data(24)
        logger.debug(f'Received for ACQ request: {header_packet}')

    def send(self, msg):
        '''Send message to the device.

        Args:
        - @msg: The message to be sent, it should be of bytes.
        '''
        self.client.send(msg)
        logger.debug(f'Sent {msg}')

    def start_acq(self):
        '''Send start acquisition message to the device.
        A thread will be started to collecting data from the device.

        Vars:
        - @data: Where the data will be stored in;
        - @data_length: The accumulated length of the data;
        - @collecting: The flag of collecting.
        '''
        self.send(struct.pack('12B', 67, 84, 82, 76,
                              0, 3, 0, 3, 0, 0, 0, 0))  # 开始采集
        self.data = []
        self.data_length = 0
        self.collecting = True

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
                self.data.append(d)
                self.data_length += d.shape[1]
                if self.data_length % 1000 == 0:
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
        if not hasattr(self, 'data'):
            return None

        if self.data == []:
            return np.zeros((self.n_channels, 0))

        return np.concatenate(self.data, axis=1)

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

    def stop_acq(self):
        '''Send stopping acquisition message to the device,
        and the collecting threading will be stopped accordingly,
        it will also clear the existing contents in the buffer.
        '''
        self.collecting = False
        time.sleep(0.1)
        self.send(struct.pack('12B', 67, 84, 82, 76,
                              0, 3, 0, 4, 0, 0, 0, 0))  # 结束采集
        self.get_data()

    def disconnect(self):
        '''Disconnect from the device.
        '''
        self.send(struct.pack('12B', 67, 84, 82, 76,
                              0, 2, 0, 2, 0, 0, 0, 0))  # 结束获取数据
        self.send(struct.pack('12B', 67, 84, 82, 76,
                              0, 1, 0, 2, 0, 0, 0, 0))  # 关闭连接
        self.client.close()
        logger.info(f'Closed Connection to Device.')
