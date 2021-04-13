import time
import socket
import struct
import threading

import numpy as np


class BaseReadData(object):
    def __init__(self, ip_address='100.1.1.79', sample_rate=1000, buffer_time=30, end_flag_trial=33):
        self.collecting = False
        self.data = []
        self.CHANNELS = [
            'FP1', 'FPZ', 'FP2', 'AF3', 'AF4', 'F7', 'F5', 'F3',
            'F1', 'FZ', 'F2', 'F4', 'F6', 'F8', 'FT7', 'FC5',
            'FC3', 'FC1', 'FCZ', 'FC2', 'FC4', 'FC6', 'FT8', 'T7',
            'C5', 'C3', 'C1', 'CZ', 'C2', 'C4', 'C6', 'T8',
            'M1', 'TP7', 'CP5', 'CP3', 'CP1', 'CPZ', 'CP2', 'CP4',
            'CP6', 'TP8', 'M2', 'P7', 'P5', 'P3', 'P1', 'PZ',
            'P2', 'P4', 'P6', 'P8', 'PO7', 'PO5', 'PO3', 'POZ',
            'PO4', 'PO6', 'PO8', 'CB1', 'O1', 'OZ', 'O2', 'CB2',
            'HEO', 'VEO', 'EKG', 'EMG'
        ]  # 所有导联 其中 M1序号为33 M2序号为43
        self.chanum = 66
        # self.chanum = len(self.CHANNELS)  # 导联数目
        print(self.chanum)
        self.sample_rate = sample_rate  # 原始采样率
        self.buffer_time = buffer_time  # 缓存区秒数
        self.buffer_point = int(
            np.round(self.sample_rate * self.buffer_time))  # 缓存区采样点数
        self.data_buffer = np.zeros(
            (self.chanum + 1, self.buffer_point))  # 数据缓存区
        self.per_packet_time = 0.04  # 每个包时长
        self.packet_time_point = int(
            np.round(self.sample_rate * self.per_packet_time))  # 每个包每导联的时间点数
        self.per_packet_bytes = (self.chanum+1) * \
            self.packet_time_point*4  # 每个包的最终的字节数

        self.ip_address = ip_address
        self.port = 4000  # 客户端端口号
        self.client = None  # 保存生成的客户端

        self._unpack_data_fmt = '<' + \
            str((self.chanum + 1) * self.packet_time_point) + 'i'  # 解码参数

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SEND_BUF_SIZE = self.per_packet_bytes
        RECV_BUF_SIZE = self.per_packet_bytes * 9

        self.client.connect((self.ip_address, self.port))
        self.client.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.client.setsockopt(
            socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUF_SIZE)
        self.client.setsockopt(
            socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_BUF_SIZE)
        print('Connect Success')

    def start_acq(self):
        """
        开始获取数据
        """
        self.client.send(struct.pack('12B', 67, 84, 82, 76,
                                     0, 2, 0, 1, 0, 0, 0, 0))  # 开始获取数据
        header_packet = self.receive_data(24)
        print(header_packet)
        print('开始从缓冲区读入数据。')
        self.client.send(struct.pack('12B', 67, 84, 82, 76,
                                     0, 3, 0, 3, 0, 0, 0, 0))  # 开始采集
        self.data = []
        self.collecting = True
        t = threading.Thread(target=self.collect)
        t.setDaemon(True)
        t.start()

    def collect(self):
        print('Collecting Start.')
        while self.collecting:
            try:
                self.data.append(self.get_data())
            except ConnectionAbortedError:
                print(
                    'Connection to the device is closed. This can be normal if collecting is done.')
                break
        print('Collecting Done.')

    def get_all(self):
        return np.concatenate(self.data, axis=1)

    def receive_data(self, n_bytes):
        """
        接收数据
        """
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
        """
        结束获取数据
        """
        self.collecting = False
        self.client.send(struct.pack('12B', 67, 84, 82, 76,
                                     0, 3, 0, 4, 0, 0, 0, 0))  # 结束采集
        time.sleep(0.001)
        self.client.send(struct.pack('12B', 67, 84, 82, 76,
                                     0, 2, 0, 2, 0, 0, 0, 0))  # 结束获取数据
        self.client.send(struct.pack('12B', 67, 84, 82, 76,
                                     0, 1, 0, 2, 0, 0, 0, 0))  # 关闭连接
        self.client.close()
        print('结束从缓冲区读入数据。')

    def _unpack_header(self, header_packet):
        """
        解码头部
        """
        chan_name = struct.unpack('>4s', header_packet[:4])
        w_code = struct.unpack('>H', header_packet[4:6])
        w_request = struct.unpack('>H', header_packet[6:8])
        packet_size = struct.unpack('>I', header_packet[8:])

        return (chan_name[0], w_code[0], w_request[0], packet_size[0])

    def _unpack_data(self, data_packet):
        """
        解码数据
        """
        data_trans = np.asarray(struct.unpack(
            self._unpack_data_fmt, data_packet)).reshape((-1, self.chanum + 1)).T

        return data_trans

    def get_data(self):
        """
        获取数据
        """

        tmp_header = self.receive_data(12)
        details_header = self._unpack_header(tmp_header)

        if details_header[-1] == self.per_packet_bytes:
            pass
        else:
            print(
                f'Warning, received data has {details_header[-1]} bytes, and required data should have {self.per_packet_bytes} bytes. The EEG channels setting may be incorrect')

        bytes_data = self.receive_data(self.per_packet_bytes)
        new_data_trans = self._unpack_data(bytes_data)

        new_data_temp = np.empty(new_data_trans.shape, dtype=np.float)
        new_data_temp[:-1, :] = new_data_trans[:-1, :] * 0.0298  # 单位 uV
        new_data_temp[-1, :] = np.zeros(new_data_trans.shape[1])

        self.new_data = new_data_temp
        return new_data_temp


if __name__ == '__main__':
    client = BaseReadData()
    client.connect()
    time.sleep(2)
    client.start_acq()
    for _ in range(5):
        time.sleep(2)
        print('-------------------------')
        print(client.get_all().shape)
    time.sleep(2)
    client.stop_acq()
    time.sleep(1)
    client.client.close()
